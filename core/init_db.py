from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from models import Role
from models.Enums import RoleType
from models.User import User
from core.config import settings
from core.security import get_password_hash


async def init_roles(session: AsyncSession):
    try:
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        if existing_roles:
            return
        roles = [
            Role(name=RoleType.student),
            Role(name=RoleType.teacher),
            Role(name=RoleType.admin)
        ]

        session.add_all(roles)
        await session.commit()

    except Exception as e:
        print(f"✗ Error initializing roles: {str(e)}")
        await session.rollback()
        raise


async def init_admin_user(session: AsyncSession):
    result = await session.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    if result.scalar_one_or_none():
        print("Admin user already exists")
        return

    admin_role = await session.execute(
        select(Role).where(Role.name == RoleType.admin)
    )
    admin_role = admin_role.scalar_one()

    admin = User(
        email=settings.ADMIN_EMAIL,
        password_hash=get_password_hash(settings.ADMIN_PASSWORD),
        first_name="Admin",
        last_name="User",
        role_id=admin_role.id
    )

    session.add(admin)
    await session.commit()


async def init_database() -> None:
    async with AsyncSessionLocal() as session:
        await init_roles(session)
        await init_admin_user(session)