from datetime import datetime
from fastapi import HTTPException
from typing import Optional
from sqlalchemy import select, and_, func
from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from helpers.students.access_helper import check_course_enrollment
from helpers.students.course_loader import load_course_with_creator
from models import User, CourseApplication, Course, CourseEnrollment
from models.Enums import ApplicationStatus
from service.course_service import check_course_access


async def get_course_applications(
        course_id: int, user: User, db: AsyncSession,
        status: Optional[ApplicationStatus] = None,
        page: int = 1, page_size: int = 20
):
    await check_course_access(course_id, user, db, require_creator=False)

    base_query = select(CourseApplication).where(
        CourseApplication.course_id == course_id
    )

    if status:
        base_query = base_query.where(CourseApplication.status == status)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    total_pages = ceil(total / page_size) if total > 0 else 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .order_by(CourseApplication.applied_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    applications = list(result.scalars().all())

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "applications": applications
    }


async def approve_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication)
        .options(selectinload(CourseApplication.course))
        .where(CourseApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    await check_course_access(application.course_id, user, db, require_creator=False)
    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application status is already '{application.status}'"
        )

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == application.user_id,
                CourseEnrollment.course_id == application.course_id
            )
        )
    )
    if enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this course"
        )

    application.status = ApplicationStatus.approved
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = user.id

    enrollment = CourseEnrollment(
        user_id=application.user_id,
        course_id=application.course_id
    )

    db.add(enrollment)
    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.id == application.id)
    )
    application_loaded = result.scalar_one()

    return {
        "id": application_loaded.id,
        "user": application_loaded.user,
        "course": application_loaded.course,
        "status": application_loaded.status,
        "applied_at": application_loaded.applied_at,
        "reviewed_at": application_loaded.reviewed_at,
        "reviewed_by": application_loaded.reviewer
    }


async def reject_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication)
        .options(selectinload(CourseApplication.course))
        .where(CourseApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    await check_course_access(application.course_id, user, db, require_creator=False)

    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application status is already '{application.status}'"
        )

    application.status = ApplicationStatus.rejected
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = user.id

    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.id == application.id)
    )
    application_loaded = result.scalar_one()

    return {
        "id": application_loaded.id,
        "user": application_loaded.user,
        "course": application_loaded.course,
        "status": application_loaded.status,
        "applied_at": application_loaded.applied_at,
        "reviewed_at": application_loaded.reviewed_at,
        "reviewed_by": application_loaded.reviewer
    }


async def apply_for_course(course_id: int, user: User, db: AsyncSession):
    course = await load_course_with_creator(course_id, db)
    enrollment = await check_course_enrollment(course_id, user, db, raise_error=False)
    if enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course"
        )
    application_result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id == course_id,
                CourseApplication.status == ApplicationStatus.pending
            )
        )
    )
    if application_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending application for this course"
        )
    application = CourseApplication(
        user_id=user.id,
        course_id=course_id,
        status=ApplicationStatus.pending
    )

    db.add(application)
    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.course).selectinload(Course.creator)
        )
        .where(CourseApplication.id == application.id)
    )
    application_with_course = result.scalar_one()

    return application_with_course


async def get_my_applications(
        user: User, db: AsyncSession,
        status: Optional[ApplicationStatus] = None,
        page: int = 1, page_size: int = 20
):
    base_query = select(CourseApplication).where(
        CourseApplication.user_id == user.id
    )

    if status:
        base_query = base_query.where(CourseApplication.status == status)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    total_pages = ceil(total / page_size) if total > 0 else 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query
        .options(
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .order_by(CourseApplication.applied_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    applications = list(result.scalars().all())

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "applications": applications
    }


async def cancel_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.id == application_id,
                CourseApplication.user_id == user.id
            )
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending applications"
        )

    await db.delete(application)
    await db.commit()
