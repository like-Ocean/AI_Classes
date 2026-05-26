from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, UploadFile
from models import (
    User, HomeworkAssignment, HomeworkSubmission,
    HomeworkSubmissionFile, LessonProgress,
)
from models.Enums import (
    HomeworkSubmissionFormat, HomeworkSubmissionStatus,
    HomeworkReviewResult,
)
from service.course_service import check_course_access
from helpers.teacher.homework_helper import (
    detect_submission_format, get_material_for_context,
    get_assignment_with_context_for_student, _serialize_submission,
    mark_material_completed_by_homework
)
from helpers.students.access_helper import require_course_enrollment
from helpers.students.progress_helper import update_course_progress_record
from service.file_service import save_file


async def create_homework_assignment(
    course_id: int, module_id: int,
    material_id: int, description: str,
    allowed_formats: List[HomeworkSubmissionFormat],
    deadline: datetime, user: User, db: AsyncSession,
) -> HomeworkAssignment:
    await check_course_access(course_id, user, db)
    await get_material_for_context(course_id, module_id, material_id, db)

    # Приводим deadline к naive datetime (убираем timezone), т.к. колонка в БД — TIMESTAMP WITHOUT TIME ZONE
    if deadline.tzinfo is not None:
        deadline = deadline.replace(tzinfo=None)

    assignment = HomeworkAssignment(
        course_id=course_id,
        module_id=module_id,
        material_id=material_id,
        created_by=user.id,
        description=description.strip(),
        allowed_formats=[fmt.value for fmt in allowed_formats],
        deadline=deadline,
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_material_homework_for_teacher(
    course_id: int, module_id: int, material_id: int, user: User, db: AsyncSession
) -> List[HomeworkAssignment]:
    await check_course_access(course_id, user, db)
    await get_material_for_context(course_id, module_id, material_id, db)

    result = await db.execute(
        select(HomeworkAssignment)
        .where(
            and_(
                HomeworkAssignment.course_id == course_id,
                HomeworkAssignment.module_id == module_id,
                HomeworkAssignment.material_id == material_id,
            )
        )
        .order_by(HomeworkAssignment.created_at.desc(), HomeworkAssignment.id.desc())
    )
    return list(result.scalars().all())


async def list_material_homework_for_student(
    course_id: int, module_id: int, material_id: int, user: User, db: AsyncSession
) -> List[HomeworkAssignment]:
    await require_course_enrollment(course_id, user, db)
    await get_material_for_context(course_id, module_id, material_id, db)

    assignments_result = await db.execute(
        select(HomeworkAssignment)
        .where(
            and_(
                HomeworkAssignment.course_id == course_id,
                HomeworkAssignment.module_id == module_id,
                HomeworkAssignment.material_id == material_id,
            )
        )
        .order_by(HomeworkAssignment.created_at.desc(), HomeworkAssignment.id.desc())
    )
    assignments = list(assignments_result.scalars().all())

    if not assignments:
        return []

    assignment_ids = [a.id for a in assignments]
    submissions_result = await db.execute(
        select(HomeworkSubmission)
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(
            and_(
                HomeworkSubmission.student_id == user.id,
                HomeworkSubmission.assignment_id.in_(assignment_ids),
            )
        )
    )
    submissions_map = {s.assignment_id: s for s in submissions_result.scalars().all()}

    now = datetime.utcnow()
    response = []
    for assignment in assignments:
        submission = submissions_map.get(assignment.id)
        if submission:
            current_status = HomeworkSubmissionStatus(submission.status)
            can_resubmit = (
                submission.review_result == HomeworkReviewResult.no_credit.value
            )
            serialized_submission = _serialize_submission(submission)
        else:
            current_status = (
                HomeworkSubmissionStatus.overdue if assignment.deadline < now else None
            )
            can_resubmit = False
            serialized_submission = None

        response.append(
            {
                "id": assignment.id,
                "course_id": assignment.course_id,
                "module_id": assignment.module_id,
                "material_id": assignment.material_id,
                "created_by": assignment.created_by,
                "description": assignment.description,
                "allowed_formats": assignment.allowed_formats,
                "deadline": assignment.deadline,
                "created_at": assignment.created_at,
                "status": current_status,
                "can_resubmit": can_resubmit,
                "submission": serialized_submission,
            }
        )

    return response


async def submit_homework(
    course_id: int, module_id: int, material_id: int,
    assignment_id: int, text_answer: Optional[str],
    files: List[UploadFile], user: User, db: AsyncSession,
) -> HomeworkSubmission:
    assignment = await get_assignment_with_context_for_student(
        course_id, module_id, material_id, assignment_id, user, db
    )

    normalized_text = (text_answer or "").strip()
    has_text = bool(normalized_text)
    has_files = len(files) > 0

    if not has_text and not has_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission must contain text and/or files",
        )

    allowed = set(assignment.allowed_formats or [])

    if has_text and HomeworkSubmissionFormat.text.value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text submission is not allowed for this homework",
        )

    uploaded_file_records = []
    for f in files:
        detected_format = detect_submission_format(f)
        if detected_format.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File format '{detected_format.value}' is not allowed for this homework",
            )
        db_file = await save_file(f, db, allow_any_extension=True)
        uploaded_file_records.append(db_file)

    result = await db.execute(
        select(HomeworkSubmission)
        .options(
            selectinload(HomeworkSubmission.files),
            selectinload(HomeworkSubmission.student)
        )
        .where(
            and_(
                HomeworkSubmission.assignment_id == assignment_id,
                HomeworkSubmission.student_id == user.id,
            )
        )
    )
    submission = result.scalar_one_or_none()

    if not submission:
        submission = HomeworkSubmission(
            assignment_id=assignment_id,
            student_id=user.id,
            text_answer=normalized_text if has_text else None,
            status=HomeworkSubmissionStatus.pending_review.value,
            updated_at=datetime.utcnow(),
        )
        db.add(submission)
        await db.flush()
    else:
        if submission.review_result == HomeworkReviewResult.credit.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Homework is already accepted and cannot be resubmitted",
            )

        submission.text_answer = normalized_text if has_text else None
        submission.status = HomeworkSubmissionStatus.pending_review.value
        submission.review_result = None
        submission.review_comment = None
        submission.reviewed_by = None
        submission.reviewed_at = None
        submission.submitted_at = datetime.utcnow()
        submission.updated_at = datetime.utcnow()
        for existing in list(submission.files):
            await db.delete(existing)

    for db_file in uploaded_file_records:
        db.add(HomeworkSubmissionFile(submission_id=submission.id, file_id=db_file.id))

    await db.commit()

    refreshed = await db.execute(
        select(HomeworkSubmission)
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(HomeworkSubmission.id == submission.id)
    )
    return refreshed.scalar_one()


async def get_my_homework_submission(
    course_id: int, module_id: int, material_id: int,
    assignment_id: int, user: User, db: AsyncSession,
) -> HomeworkSubmission:
    await get_assignment_with_context_for_student(
        course_id, module_id, material_id, assignment_id, user, db
    )

    result = await db.execute(
        select(HomeworkSubmission)
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(
            and_(
                HomeworkSubmission.assignment_id == assignment_id,
                HomeworkSubmission.student_id == user.id,
            )
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework submission not found",
        )
    return submission


async def list_homework_submissions_for_teacher(
    course_id: int, module_id: int,
    material_id: int, assignment_id: int,
    user: User, db: AsyncSession,
    search: Optional[str] = None,
    submission_status: Optional[HomeworkSubmissionStatus] = None,
    review_result: Optional[HomeworkReviewResult] = None,
    sort_by: str = "updated_at", order: str = "desc",
    page: int = 1, page_size: int = 50,
) -> dict:
    await check_course_access(course_id, user, db)

    assignment_result = await db.execute(
        select(HomeworkAssignment).where(
            and_(
                HomeworkAssignment.id == assignment_id,
                HomeworkAssignment.course_id == course_id,
                HomeworkAssignment.module_id == module_id,
                HomeworkAssignment.material_id == material_id,
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework assignment not found",
        )

    base_query = select(HomeworkSubmission)
    if search:
        base_query = base_query.join(User, HomeworkSubmission.student_id == User.id)

    filters = [HomeworkSubmission.assignment_id == assignment_id]
    if submission_status is not None:
        filters.append(HomeworkSubmission.status == submission_status.value)
    if review_result is not None:
        filters.append(HomeworkSubmission.review_result == review_result.value)
    if search:
        search_value = f"%{search}%"
        filters.append(
            or_(
                User.first_name.ilike(search_value),
                User.last_name.ilike(search_value),
                User.patronymic.ilike(search_value),
                User.email.ilike(search_value),
            )
        )

    count_query = select(func.count()).select_from(
        base_query.where(and_(*filters)).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = ceil(total / page_size) if total > 0 else 0

    sort_key_map = {
        "submitted_at": HomeworkSubmission.submitted_at,
        "updated_at": HomeworkSubmission.updated_at,
        "status": HomeworkSubmission.status,
        "review_result": HomeworkSubmission.review_result,
    }
    sort_column = sort_key_map.get(sort_by, HomeworkSubmission.updated_at)
    order_by = sort_column.asc() if order.lower() == "asc" else sort_column.desc()

    submissions_result = await db.execute(
        base_query
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(and_(*filters))
        .order_by(order_by, HomeworkSubmission.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    submissions = list(submissions_result.scalars().all())

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "submissions": [_serialize_submission(sub) for sub in submissions],
    }


async def review_homework_submission(
    course_id: int, module_id: int, material_id: int,
    assignment_id: int, submission_id: int,
    review_result: HomeworkReviewResult,
    review_comment: Optional[str],
    user: User, db: AsyncSession,
) -> dict:
    await check_course_access(course_id, user, db)

    result = await db.execute(
        select(HomeworkSubmission)
        .join(
            HomeworkAssignment,
            HomeworkAssignment.id == HomeworkSubmission.assignment_id,
        )
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(
            and_(
                HomeworkSubmission.id == submission_id,
                HomeworkSubmission.assignment_id == assignment_id,
                HomeworkAssignment.course_id == course_id,
                HomeworkAssignment.module_id == module_id,
                HomeworkAssignment.material_id == material_id,
            )
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework submission not found",
        )

    submission.status = HomeworkSubmissionStatus.reviewed.value
    submission.review_result = review_result.value
    submission.review_comment = (review_comment or "").strip() or None
    submission.reviewed_by = user.id
    submission.reviewed_at = datetime.utcnow()
    submission.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(submission)

    if review_result == HomeworkReviewResult.credit:
        assignment = await db.get(HomeworkAssignment, submission.assignment_id)
        if assignment:
            await mark_material_completed_by_homework(
                user_id=submission.student_id,
                material_id=assignment.material_id,
                course_id=assignment.course_id,
                db=db,
            )

    refreshed = await db.execute(
        select(HomeworkSubmission)
        .options(
            selectinload(HomeworkSubmission.files).selectinload(
                HomeworkSubmissionFile.file
            ),
            selectinload(HomeworkSubmission.student)
        )
        .where(HomeworkSubmission.id == submission.id)
    )
    return _serialize_submission(refreshed.scalar_one())
