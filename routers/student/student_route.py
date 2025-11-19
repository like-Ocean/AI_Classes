from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from core.database import get_db
from core.dependencies import get_current_user
from service import student_service, student_test_service
from models import User
from schemas.student import (
    CourseApplicationResponse, PaginatedCoursesResponse,
    MyCoursesResponse, LessonProgressResponse,
    ModuleWithProgressResponse, CourseCardResponse,
    CourseModulesWithProgressResponse
)
from schemas.student_tests import (
    TestForStudent, TestAttemptResponse, SubmitAnswerRequest,
    QuestionAttemptResponse, TestResultResponse, MyTestAttemptSummary,
    TestAttemptWithBlockResponse
)
from schemas.course import CourseWithModulesResponse
from schemas.auth import MessageResponse

student_router = APIRouter(prefix="/students", tags=["Student"])


# COURSE CATALOG
@student_router.get(
    "/courses",
    response_model=PaginatedCoursesResponse,
    summary="Get available courses catalog"
)
async def get_courses_catalog(
        search: Optional[str] = Query(
            None,
            description="Поиск по названию или описанию"
        ),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_available_courses(
        user=current_user, db=db, search=search,
        page=page, page_size=page_size
    )
    return data


@student_router.get(
    "/courses/{course_id}",
    response_model=CourseCardResponse,
    summary="Get course public info"
)
async def get_course_public_info(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_course_public_detail(
        course_id, current_user, db
    )
    return data


# APPLICATIONS

@student_router.post(
    "/courses/{course_id}/apply",
    response_model=CourseApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for course"
)
async def apply_for_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    application = await student_service.apply_for_course(
        course_id, current_user, db
    )
    return application


@student_router.get(
    "/applications",
    response_model=list[CourseApplicationResponse],
    summary="Get my applications"
)
async def get_my_applications(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    applications = await student_service.get_my_applications(
        current_user, db
    )
    return applications


@student_router.delete(
    "/applications/{application_id}",
    response_model=MessageResponse,
    summary="Cancel application"
)
async def cancel_application(
        application_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await student_service.cancel_application(
        application_id, current_user, db
    )
    return MessageResponse(message="Application cancelled successfully")


# MY COURSES

@student_router.get(
    "/my-courses",
    response_model=MyCoursesResponse,
    summary="Get my enrolled courses"
)
async def get_my_courses(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_my_courses(
        current_user, db
    )
    return data


# Возможно нужно удалить так как есть get_course_modules(Get all course modules with progress)
@student_router.get(
    "/my-courses/{course_id}",
    response_model=CourseWithModulesResponse,
    summary="Get enrolled course details"
)
async def get_enrolled_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    course = await student_service.get_enrolled_course_detail(
        course_id, current_user, db
    )
    return course


@student_router.get(
    "/my-courses/{course_id}/modules/{module_id}",
    response_model=ModuleWithProgressResponse,
    summary="Get module with progress"
)
async def get_module(
    course_id: int, module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_module_with_progress(
        course_id, module_id, current_user, db
    )
    return data


@student_router.get(
    "/my-courses/{course_id}/modules",
    response_model=CourseModulesWithProgressResponse,
    summary="Get all course modules with progress"
)
async def get_course_modules(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_course_modules_with_progress(
        course_id, current_user, db
    )
    return data


# PROGRESS
@student_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/complete",
    response_model=LessonProgressResponse,
    summary="Mark material as completed"
)
async def complete_material(
    course_id: int, module_id: int,
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    progress = await student_service.mark_material_completed(
        course_id, module_id, material_id, current_user, db
    )
    return progress


# TESTS
@student_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}",
    response_model=TestForStudent,
    summary="Get test for taking"
)
async def get_test(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    test = await student_test_service.get_test_for_student(
        course_id, module_id, material_id,
        test_id, current_user, db
    )
    return test


@student_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/start",
    response_model=TestAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start test attempt"
)
async def start_test(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attempt = await student_test_service.start_test_attempt(
        course_id, module_id, material_id,
        test_id, current_user, db
    )
    return attempt


@student_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/answer",
    response_model=QuestionAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit answer to question"
)
async def submit_answer(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    attempt_id: int, data: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    question_attempt = await student_test_service.submit_answer(
        course_id, module_id, material_id, test_id, attempt_id,
        data.question_id, data.answer, data.hint_used, current_user, db
    )
    return question_attempt


@student_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/finish",
    response_model=TestAttemptWithBlockResponse,
    summary="Finish test attempt"
)
async def finish_test(
    course_id: int,
    module_id: int,
    material_id: int,
    test_id: int,
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await student_test_service.finish_test_attempt(
        course_id, module_id, material_id,
        test_id, attempt_id, current_user, db
    )
    return result


@student_router.get(
    "/test-attempts/{attempt_id}/result",
    response_model=TestResultResponse,
    summary="Get test result"
)
async def get_result(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await student_test_service.get_test_result(
        attempt_id, current_user, db
    )
    return result


@student_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts",
    response_model=List[MyTestAttemptSummary],
    summary="Get my test attempts"
)
async def get_my_attempts(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attempts = await student_test_service.get_my_test_attempts(
        course_id, module_id, material_id, test_id, current_user, db
    )
    return attempts
