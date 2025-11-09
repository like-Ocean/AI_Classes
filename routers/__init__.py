from .auth import auth_route
from .user import user_route
from .admin import admin_route
from .teacher import teacher_route
from .test import test_route
from .student import student_route
from .AI import ai_route

routes = [
    auth_route.auth_router,
    user_route.user_router,
    admin_route.admin_router,
    teacher_route.teacher_router,
    test_route.test_router,
    student_route.student_router,
    ai_route.ai_router
]
