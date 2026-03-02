import os
import uuid
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.db.session import get_db, SessionLocal
from app.core.config import settings
from app.core.storage import storage # Use the new storage abstraction
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.rag.models import Document, Project, ChatSession, ChatMessage
from app.modules.rag.service import rag_service
from app.modules.rag.schemas import ProjectRead, DocumentRead, ChatSessionRead, MessageRead
from app.modules.jobs.models import Job, JobStatus
from app.worker.redis_queue import job_queue
from app.worker.tasks import process_job
from rq import Retry

router = APIRouter()

# --- SCHEMAS ---
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DocumentUpdate(BaseModel):
    project_id: Optional[uuid.UUID] = None
    filename: Optional[str] = None

class BulkMoveRequest(BaseModel):
    document_ids: List[uuid.UUID]
    project_id: uuid.UUID

class BulkDeleteRequest(BaseModel):
    document_ids: List[uuid.UUID]
    permanent: bool = False

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None

class ChatCreate(BaseModel):
    project_id: Optional[uuid.UUID] = None
    selected_document_ids: List[str]
    title: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str

# --- SAVE MESSAGE HELPER ---
def save_chat_message(session_id: uuid.UUID, role: str, content: str, sources: Optional[List[Dict]] = None):
    db = SessionLocal()
    try:
        msg = ChatMessage(session_id=session_id, role=role, content=content, sources=sources)
        db.add(msg)
        db.commit()
    finally:
        db.close()

# --- PROJECT ENDPOINTS ---

@router.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = Project(user_id=current_user.id, name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/projects", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Project).filter(Project.user_id == current_user.id).order_by(desc(Project.created_at)).all()

@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project: raise HTTPException(404, "Project not found")
    if payload.name: project.name = payload.name
    if payload.description is not None: project.description = payload.description
    db.commit()
    db.refresh(project)
    return project

@router.delete("/projects/{project_id}")
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project: raise HTTPException(404, "Project not found")
    db.query(Document).filter(Document.project_id == project_id).update({"project_id": None})
    db.delete(project)
    db.commit()
    return {"message": "Success"}

# --- DOCUMENT ENDPOINTS ---

@router.get("/documents", response_model=List[DocumentRead])
def list_all_documents(project_id: Optional[uuid.UUID] = Query(None), only_unassigned: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if project_id: query = query.filter(Document.project_id == project_id)
    if only_unassigned: query = query.filter(Document.project_id == None)
    return query.order_by(desc(Document.created_at)).all()

@router.get("/documents/{doc_id}/file")
def get_document_file(doc_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Document not found")
    
    # If S3, we download to a temporary file then serve
    import tempfile
    file_key = f"{doc.id}.pdf"
    
    if settings.USE_S3:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        storage.download_file(file_key, temp_file.name)
        return FileResponse(temp_file.name, media_type="application/pdf", filename=doc.filename)
    else:
        if not os.path.exists(doc.file_path): raise HTTPException(404, "File not found")
        return FileResponse(doc.file_path, media_type="application/pdf")

@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...), project_id: Optional[uuid.UUID] = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "error", "message": "Only PDFs allowed"})
            continue
        
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        existing_doc = db.query(Document).filter(Document.user_id == current_user.id, Document.file_hash == file_hash).first()
        if existing_doc:
            if project_id and existing_doc.project_id is None:
                existing_doc.project_id = project_id
                db.commit()
                results.append({"filename": file.filename, "status": "assigned", "document_id": str(existing_doc.id)})
            else:
                results.append({"filename": file.filename, "status": "existing", "document_id": str(existing_doc.id)})
            continue
        
        file_id = uuid.uuid4()
        file_key = f"{file_id}.pdf"
        
        # UPLOAD TO S3 OR LOCAL
        storage_path = storage.upload_file(content, file_key)
        
        db_doc = Document(
            id=file_id, 
            user_id=current_user.id, 
            project_id=project_id, 
            filename=file.filename, 
            file_path=storage_path, 
            file_size=len(content), 
            file_hash=file_hash
        )
        db.add(db_doc)
        
        db_job = Job(user_id=current_user.id, status=JobStatus.PENDING.value, job_type="rag_ingestion", job_metadata={"document_id": str(db_doc.id)})
        db.add(db_job)
        db.commit()
        
        job_queue.enqueue(process_job, str(db_job.id), retry=Retry(max=2), job_timeout=600)
        results.append({"filename": file.filename, "status": "queued", "document_id": str(db_doc.id)})
    return results

@router.post("/documents/bulk-delete")
def bulk_delete_documents(payload: BulkDeleteRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.id.in_(payload.document_ids), Document.user_id == current_user.id).all()
    if payload.permanent:
        for doc in docs:
            background_tasks.add_task(rag_service.delete_document_vectors, str(current_user.id), str(doc.id))
            # Delete from S3/Local
            storage.delete_file(f"{doc.id}.pdf")
            db.delete(doc)
    else:
        db.query(Document).filter(Document.id.in_(payload.document_ids)).update({"project_id": None}, synchronize_session=False)
    db.commit()
    return {"message": "Success"}

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: uuid.UUID, background_tasks: BackgroundTasks, permanent: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Document not found")
    if permanent:
        background_tasks.add_task(rag_service.delete_document_vectors, str(current_user.id), str(doc.id))
        storage.delete_file(f"{doc.id}.pdf")
        db.delete(doc)
    else:
        doc.project_id = None
    db.commit()
    return {"message": "Success"}

# --- CHAT ENDPOINTS ---

@router.post("/chats", response_model=ChatSessionRead)
def create_chat_session(payload: ChatCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    title = payload.title
    if not title:
        if payload.project_id:
            project = db.query(Project).filter(Project.id == payload.project_id, Project.user_id == current_user.id).first()
            title = project.name if project else "Project Chat"
        else:
            docs = db.query(Document).filter(Document.id.in_(payload.selected_document_ids)).limit(2).all()
            doc_names = [d.filename.replace('.pdf', '') for d in docs]
            title = ", ".join(doc_names)
            if len(payload.selected_document_ids) > 2: title += f" + {len(payload.selected_document_ids) - 2} more"
            if not title: title = "New Chat"
    session = ChatSession(user_id=current_user.id, project_id=payload.project_id, title=title, selected_document_ids=payload.selected_document_ids)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/chats", response_model=List[ChatSessionRead])
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(desc(ChatSession.is_pinned), desc(ChatSession.created_at)).all()

@router.patch("/chats/{session_id}", response_model=ChatSessionRead)
def update_chat_session(session_id: uuid.UUID, payload: ChatUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session: raise HTTPException(404, "Chat not found")
    if payload.title is not None: session.title = payload.title
    if payload.is_pinned is not None: session.is_pinned = payload.is_pinned
    db.commit()
    db.refresh(session)
    return session

@router.delete("/chats/{session_id}")
def delete_chat_session(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session: raise HTTPException(404, "Chat not found")
    db.delete(session)
    db.commit()
    return {"message": "Success"}

@router.get("/chats/{session_id}/messages", response_model=List[MessageRead])
def get_chat_history(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session: raise HTTPException(404, "Chat not found")
    return session.messages

@router.post("/chats/{session_id}/ask")
async def ask_in_session(
    session_id: uuid.UUID,
    payload: QuestionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session: raise HTTPException(404, "Chat session not found")
    
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    doc_id_to_name = {str(d.id): d.filename for d in docs}
    
    history = [{"role": m.role, "content": m.content} for m in session.messages]
    
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.question)
    db.add(user_msg)
    db.commit()

    gen, sources = rag_service.ask_question_stream(
        user_id=str(current_user.id),
        question=payload.question,
        selected_document_ids=session.selected_document_ids,
        chat_history=history,
        doc_id_to_name=doc_id_to_name
    )

    def generate():
        full_response = ""
        for chunk in gen:
            full_response += chunk
            yield chunk
        background_tasks.add_task(save_chat_message, session.id, "assistant", full_response, sources)

    return StreamingResponse(generate(), media_type="text/plain")
