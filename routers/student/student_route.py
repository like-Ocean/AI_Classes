from fastapi import APIRouter
from .catalog_route import student_catalog_router
from .test_route import student_test_router
from .comment_route import student_comment_router
from .homework_route import student_homework_router

student_router = APIRouter(prefix="/students")
student_router.include_router(student_catalog_router)
student_router.include_router(student_test_router)
student_router.include_router(student_comment_router)
student_router.include_router(student_homework_router)
