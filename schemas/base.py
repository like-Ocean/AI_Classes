from pydantic import BaseModel


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
