from fastapi import APIRouter
from .catalog_route import student_catalog_router
from .test_route import student_test_router

student_router = APIRouter(prefix="/students", tags=["Student"])
student_router.include_router(student_catalog_router)
student_router.include_router(student_test_router)
