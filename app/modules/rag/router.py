import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.rag.models import Document
from app.modules.jobs.models import Job, JobStatus
from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job
from rq import Retry

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    file_id = uuid.uuid4()
    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    # Save to disk
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create Document record
    db_doc = Document(
        id=file_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        status="processing"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Create Job record for tracking
    db_job = Job(
        user_id=current_user.id,
        status=JobStatus.PENDING.value,
        job_type="rag_ingestion",
        job_metadata={"document_id": str(db_doc.id)}
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Enqueue Worker Task
    job_queue.enqueue(
        process_job,
        str(db_job.id),
        retry=Retry(max=2),
        job_timeout=600 # 10 minutes for large PDFs
    )

    return {
        "document_id": str(db_doc.id),
        "job_id": str(db_job.id),
        "status": "queued"
    }

from pydantic import BaseModel
from app.modules.rag.service import rag_service

class QuestionRequest(BaseModel):
    question: str

@router.post("/ask")
def ask_document(
    payload: QuestionRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        result = rag_service.ask_question(str(current_user.id), payload.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@router.get("/documents")
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "page_count": d.page_count,
            "created_at": d.created_at
        }
        for d in docs
    ]
