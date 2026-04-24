from typing import Dict, Optional
from models import CourseProgress, Course
from models.Enums import ApplicationStatus


def format_progress_data(progress: CourseProgress) -> Optional[Dict]:
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
    course: Course,
    progress_data: Optional[Dict] = None,
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
