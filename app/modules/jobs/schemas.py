from pydantic import BaseModel
from datetime import datetime

class JobListItem(BaseModel):
    id: str
    status: str
    job_type: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobListResponse(BaseModel):
    total: int
    items: list[JobListItem]
