from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from models import CourseEnrollment, CourseApplication, CourseProgress
from models.Enums import ApplicationStatus
from typing import List, Optional


async def load_user_enrollments(user_id: int, db: AsyncSession) -> List[CourseEnrollment]:
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.course))
        .where(CourseEnrollment.user_id == user_id)
        .order_by(CourseEnrollment.id.desc())
    )
    return list(result.scalars().all())


async def load_pending_applications(user_id: int, db: AsyncSession) -> List[CourseApplication]:
    result = await db.execute(
        select(CourseApplication)
        .options(selectinload(CourseApplication.course))
        .where(
            and_(
                CourseApplication.user_id == user_id,
                CourseApplication.status == ApplicationStatus.pending
            )
        )
        .order_by(CourseApplication.applied_at.desc())
    )
    return list(result.scalars().all())


async def get_course_progress(user_id: int, course_id: int, db: AsyncSession) -> Optional[CourseProgress]:
    result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id
            )
        )
    )
    return result.scalar_one_or_none()
