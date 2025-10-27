from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status
from typing import Optional
from models import User, Role, Course, CourseEnrollment, CourseApplication
from models.Enums import RoleType
from core.security import get_password_hash
from schemas.admin import (
    CreateUserRequest, UpdateUserRequest,
    StatisticsResponse
)


# возможно сделать чтобы после создания пользователя с указанной
# почтой на неё приходило уведомление о томы что вы были зареганы
async def create_user(data: CreateUserRequest, db: AsyncSession):
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    result = await db.execute(
        select(Role).where(Role.name == data.role)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {data.role} not found"
        )

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        group_name=data.group_name,
        role_id=role.id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def get_users_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        role_filter: Optional[RoleType] = None,
        search: Optional[str] = None
):
    query = select(User)

    if role_filter:
        result = await db.execute(select(Role).where(Role.name == role_filter))
        role = result.scalar_one_or_none()
        if role:
            query = query.where(User.role_id == role.id)

    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return list(users), total


async def get_user_by_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


async def update_user(user_id: int, data: UpdateUserRequest, db: AsyncSession):
    user = await get_user_by_id(user_id, db)

    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.patronymic is not None:
        user.patronymic = data.patronymic
    if data.group_name is not None:
        user.group_name = data.group_name

    if data.role is not None:
        result = await db.execute(select(Role).where(Role.name == data.role))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role {data.role} not found"
            )
        user.role_id = role.id

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(user_id: int, current_admin: User, db: AsyncSession):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself"
        )

    user = await get_user_by_id(user_id, db)

    await db.delete(user)
    await db.commit()


async def change_user_role(
        user_id: int,
        new_role: RoleType,
        current_admin: User,
        db: AsyncSession
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )

    user = await get_user_by_id(user_id, db)

    result = await db.execute(
        select(Role).where(Role.name == new_role)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {new_role} not found"
        )

    user.role_id = role.id

    await db.commit()
    await db.refresh(user)

    return user


async def get_statistics(db: AsyncSession):
    total_users_result = await db.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar()

    student_role_result = await db.execute(
        select(Role).where(Role.name == RoleType.student)
    )
    student_role = student_role_result.scalar_one_or_none()

    total_students = 0
    if student_role:
        students_result = await db.execute(
            select(
                func.count(User.id)
            ).where(User.role_id == student_role.id)
        )
        total_students = students_result.scalar()

    teacher_role_result = await db.execute(
        select(Role).where(Role.name == RoleType.teacher)
    )
    teacher_role = teacher_role_result.scalar_one_or_none()

    total_teachers = 0
    if teacher_role:
        teachers_result = await db.execute(
            select(
                func.count(User.id)
            ).where(User.role_id == teacher_role.id)
        )
        total_teachers = teachers_result.scalar()

    courses_result = await db.execute(
        select(func.count(Course.id))
    )
    total_courses = courses_result.scalar()

    enrollments_result = await db.execute(
        select(func.count(CourseEnrollment.id))
    )
    total_enrollments = enrollments_result.scalar()

    pending_applications_result = await db.execute(
        select(func.count(CourseApplication.id)).where(
            CourseApplication.status == "pending"
        )
    )
    total_applications_pending = pending_applications_result.scalar()

    return StatisticsResponse(
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        total_applications_pending=total_applications_pending
    )
