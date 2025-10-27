from .auth import auth_route
from .user import user_route
from .admin import admin_route

routes = [
    auth_route.auth_router,
    user_route.user_router,
    admin_route.admin_router
]
