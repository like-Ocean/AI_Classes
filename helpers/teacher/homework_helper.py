from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil
from sqlalchemy import select, and_
from fastapi import HTTPException, status, UploadFile
from models import (
    User, Module, Material,
    HomeworkAssignment, HomeworkSubmission, LessonProgress,
)
from models.Enums import (HomeworkSubmissionFormat)
from helpers.general.common_helper import _build_full_name
from helpers.students.access_helper import require_course_enrollment
from helpers.students.progress_helper import update_course_progress_record


def detect_submission_format(upload_file: UploadFile) -> HomeworkSubmissionFormat:
    mime = (upload_file.content_type or "").lower()
    if mime.startswith("video/"):
        return HomeworkSubmissionFormat.video
    if mime.startswith("image/"):
        return HomeworkSubmissionFormat.photo
    return HomeworkSubmissionFormat.files


async def get_material_for_context(
    course_id: int, module_id: int, material_id: int, db: AsyncSession
) -> Material:
    result = await db.execute(
        select(Material)
        .join(Module, Module.id == Material.module_id)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id,
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module",
        )
    return material



async def get_assignment_with_context_for_student(
    course_id: int, module_id: int, material_id: int,
    assignment_id: int, user: User, db: AsyncSession,
) -> HomeworkAssignment:
    await require_course_enrollment(course_id, user, db)

    result = await db.execute(
        select(HomeworkAssignment).where(
            and_(
                HomeworkAssignment.id == assignment_id,
                HomeworkAssignment.course_id == course_id,
                HomeworkAssignment.module_id == module_id,
                HomeworkAssignment.material_id == material_id,
            )
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework assignment not found",
        )
    return assignment


def _serialize_submission(submission: HomeworkSubmission) -> dict:
    student = submission.student
    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "full_name": _build_full_name(student) if student else None,
        "group_name": student.group_name if student else None,
        "text_answer": submission.text_answer,
        "status": submission.status,
        "review_result": submission.review_result,
        "review_comment": submission.review_comment,
        "reviewed_by": submission.reviewed_by,
        "reviewed_at": submission.reviewed_at,
        "submitted_at": submission.submitted_at,
        "updated_at": submission.updated_at,
        "files": [sf.file for sf in submission.files],
    }


async def mark_material_completed_by_homework(
    user_id: int, material_id: int, course_id: int, db: AsyncSession
):
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == material_id,
            )
        )
    )
    existing = progress_result.scalar_one_or_none()
    if not existing:
        db.add(LessonProgress(user_id=user_id, lesson_id=material_id))
        await db.commit()

    await update_course_progress_record(user_id, course_id, db)