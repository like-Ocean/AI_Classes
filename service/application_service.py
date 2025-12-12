from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from models import User, CourseApplication, Course, CourseEnrollment
from models.Enums import ApplicationStatus
from service.course_service import check_course_access


async def get_course_applications(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=False)
    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.course_id == course_id)
        .order_by(CourseApplication.applied_at.desc())
    )
    return list(result.scalars().all())


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
