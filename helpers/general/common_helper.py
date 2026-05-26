from models import User


def _build_full_name(user: User) -> str:
    parts = [user.last_name, user.first_name, user.patronymic]
    return " ".join(p for p in parts if p)