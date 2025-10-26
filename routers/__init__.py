from .auth import auth
from .user import user

routes = [
    auth.auth_router,
    user.user_router
]
