from pydantic import BaseModel
from datetime import datetime
from typing import List
from schemas.base import ORMModel


class FileResponse(ORMModel):
    id: int
    filename: str
    original_filename: str
    file_url: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

class MaterialFileResponse(ORMModel):
    id: int
    material_id: int
    file: FileResponse

