from .auth import auth_route
from .user import user_route
from .admin import admin_route
from .teacher import teacher_route

routes = [
    auth_route.auth_router,
    user_route.user_router,
    admin_route.admin_router,
    teacher_route.teacher_router
]
