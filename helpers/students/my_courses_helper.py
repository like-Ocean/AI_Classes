from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from models import CourseEnrollment, CourseApplication, CourseProgress
from models.Enums import ApplicationStatus
from typing import List, Optional, Dict


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


def format_progress_data(progress: CourseProgress) -> Dict:
    if not progress:
        return None

    progress_percentage = (
        (progress.completed_items / progress.total_items * 100)
        if progress.total_items > 0 else 0
    )

    return {
        "id": progress.id,
        "course_id": progress.course_id,
        "user_id": progress.user_id,
        "completed_items": progress.completed_items,
        "total_items": progress.total_items,
        "progress_percentage": round(progress_percentage, 2),
        "last_accessed_at": progress.last_accessed_at
    }


def format_course_card(
        course, progress_data: Optional[Dict] = None,
        application_status: Optional[ApplicationStatus] = None
) -> Dict:
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "img_url": course.img_url,
        "progress": progress_data,
        "application_status": application_status
    }
