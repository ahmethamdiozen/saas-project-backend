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
        logger.info(f"Worker picked up Job: {job_id}")
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} status set to RUNNING")

        if job.job_type == "rag_ingestion":
            doc_id = job.job_metadata.get("document_id")
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        file_key = f"{doc.id}.pdf"
                        logger.info(f"Downloading {file_key} from S3...")
                        download_path = storage.download_file(file_key, tmp.name)
                        
                        logger.info(f"Processing document: {doc.filename}")
                        page_count = rag_service.process_document(
                            download_path, 
                            str(doc.id), 
                            str(doc.user_id),
                            doc.filename
                        )
                        
                        doc.status = "ready"
                        doc.page_count = page_count
                        db.commit() # Commit document status change immediately
                        logger.info(f"Document {doc.id} marked as READY")
                        
                        if os.path.exists(download_path):
                            os.remove(download_path)
                            
                except Exception as e:
                    db.rollback()
                    error_trace = traceback.format_exc()
                    logger.error(f"Internal error during document processing {doc_id}: {str(e)}\n{error_trace}")
                    doc.status = "error"
                    db.commit()
            
        job.status = JobStatus.SUCCESS.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        db.rollback()
        if job:
            job.status = JobStatus.FAILED.value
            db.commit()
        logger.error(f"Fatal worker error for Job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()
