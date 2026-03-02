from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

class DocumentRead(BaseModel):
    id: UUID
    filename: str
    status: str
    page_count: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    documents: List[DocumentRead] = []
    
    model_config = ConfigDict(from_attributes=True)

class MessageRead(BaseModel):
    id: UUID
    role: str
    content: str
    sources: Optional[Any] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatSessionRead(BaseModel):
    id: UUID
    title: str
    is_pinned: bool
    selected_document_ids: List[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
