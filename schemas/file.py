from pydantic import BaseModel
from datetime import datetime
from typing import List


class FileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_url: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class MaterialFileResponse(BaseModel):
    id: int
    material_id: int
    file: FileResponse

    class Config:
        from_attributes = True
