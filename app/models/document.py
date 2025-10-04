from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    PPT = "ppt"

class DocumentBase(BaseModel):
    filename: str
    file_type: DocumentType
    file_size: int

class DocumentCreate(DocumentBase):
    user_id: str

class DocumentUpdate(BaseModel):
    filename: Optional[str] = None

class DocumentInDB(DocumentBase):
    id: int
    user_id: str
    upload_date: datetime
    extracted_text: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: int
    user_id: str
    upload_date: datetime
    text_preview: Optional[str] = None

    class Config:
        from_attributes = True