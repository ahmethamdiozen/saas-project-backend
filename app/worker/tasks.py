import os
import tempfile
import traceback
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.jobs.models import Job, JobStatus
from app.modules.rag.models import Document
from app.modules.rag.service import rag_service
from app.core.storage import storage
from app.core.logging import logger

def process_job(job_id: str):
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Use datetime objects instead of integers for Postgres
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        if job.job_type == "rag_ingestion":
            doc_id = job.job_metadata.get("document_id")
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        file_key = f"{doc.id}.pdf"
                        logger.info(f"Downloading {file_key} from S3 for processing...")
                        download_path = storage.download_file(file_key, tmp.name)
                        
                        logger.info(f"Starting RAG ingestion for {doc.filename}")
                        page_count = rag_service.process_document(
                            download_path, 
                            str(doc.id), 
                            str(doc.user_id),
                            doc.filename
                        )
                        
                        doc.status = "ready"
                        doc.page_count = page_count
                        
                        if os.path.exists(download_path):
                            os.remove(download_path)
                        logger.info(f"Successfully processed {doc.filename}")
                            
                except Exception as e:
                    error_trace = traceback.format_exc()
                    logger.error(f"RAG Processing failed for {doc_id}: {str(e)}\n{error_trace}")
                    doc.status = "error"
            
        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc) # Correct field name is finished_at
        db.commit()

    except Exception as e:
        db.rollback()
        if job:
            job.status = JobStatus.FAILED.value
            db.commit()
        logger.error(f"Job {job_id} failed: {str(e)}")
    finally:
        db.close()
