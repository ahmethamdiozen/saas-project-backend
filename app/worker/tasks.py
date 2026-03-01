from datetime import datetime, timezone
import time
import os

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.logging import logger
from app.modules.jobs.models import Job, JobResult, JobStatus, JobExecution
from app.modules.rag.models import Document
from app.modules.rag.service import rag_service
from app.worker.locks import acquire_job_lock, release_job_lock
from app.worker.cancellation import (
    CancellationToken, 
    register_token,
    unregister_token,
    JobCancelledError
)


SLOW_EXECUTION_THRESHOLD = 30 # RAG can take time

def process_job(job_id: str):

    token = CancellationToken()
    register_token(job_id, token)

    if not acquire_job_lock(job_id):
        logger.warning(f"Job {job_id} already running")
        return
    
    db = None
    execution = None
    document = None # Pre-initialize to avoid UnboundLocalError
    
    try:
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job or job.status in (JobStatus.SUCCESS.value, JobStatus.FAILED.value):
            return
        
        # Get associated document from job_metadata
        doc_id = job.job_metadata.get("document_id") if job.job_metadata else None
        document = db.query(Document).filter(Document.id == doc_id).first() if doc_id else None

        if not document:
            logger.error(f"No document found for job {job_id}")
            return

        attempt_number = len(job.executions) + 1
        execution = JobExecution(
            job_id = job.id,
            attempt_number=attempt_number,
            status=JobStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc)
        )
        db.add(execution)
        db.commit()

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # --- RAG PIPELINE ---
        
        token.raise_if_cancelled()
        # STEP 1: Extraction
        execution.current_step = "extracting_text"
        execution.progress = 20
        db.commit()
        
        # We perform actual extraction
        pages_content = rag_service.extract_text_from_pdf(document.file_path)
        document.page_count = len(pages_content)
        db.commit()

        token.raise_if_cancelled()
        # STEP 2: Chunking & Embedding
        execution.current_step = "generating_embeddings"
        execution.progress = 60
        db.commit()
        
        # This will store in ChromaDB
        rag_service.process_document(document.file_path, str(document.id), str(job.user_id))

        token.raise_if_cancelled()
        # STEP 3: Finalizing
        execution.current_step = "finalizing"
        execution.progress = 90
        db.commit()

        # Success
        execution.status = JobStatus.SUCCESS.value
        execution.progress = 100
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration_seconds = (execution.finished_at - execution.started_at).total_seconds()
        
        document.status = "ready"
        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc)
        
        db.commit()
        logger.info(f"RAG processing complete for document {document.id}")

    except Exception as e:
        logger.error(f"RAG Job failed: {str(e)}", exc_info=True)
        if db:
            db.rollback()
            if execution:
                execution.status = JobStatus.FAILED.value
                execution.error_message = str(e)
                execution.finished_at = datetime.now(timezone.utc)
            if job:
                job.status = JobStatus.FAILED.value
            if document:
                document.status = "error"
            db.commit()
        raise
    finally:
        release_job_lock(job_id)
        if db: db.close()
        unregister_token(job_id)