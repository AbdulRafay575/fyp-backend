from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SummaryBase(BaseModel):
    title: str
    content: str
    source_text: Optional[str] = None
    source_type: str  # document, youtube, etc.

class SummaryCreate(SummaryBase):
    user_id: str
    document_id: Optional[int] = None

class SummaryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class SummaryInDB(SummaryBase):
    id: int
    user_id: str
    document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SummaryResponse(SummaryBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True