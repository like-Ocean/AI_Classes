from fastapi import APIRouter
from .course_route import teacher_course_router
from .management_route import teacher_management_router
from .homework_route import teacher_homework_router

teacher_router = APIRouter(prefix="/teacher")
teacher_router.include_router(teacher_course_router)
teacher_router.include_router(teacher_management_router)
teacher_router.include_router(teacher_homework_router)
