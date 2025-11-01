from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import (
    Course, Module, Material, CourseEditor,
    User, Role, MaterialFile, File
)
from models.Enums import RoleType
from schemas.course import (
    CourseCreateRequest, CourseUpdateRequest, ModuleCreateRequest,
    ModuleUpdateRequest, MaterialCreateRequest, MaterialUpdateRequest
)


async def check_course_access(
        course_id: int, user: User,
        db: AsyncSession, require_creator: bool = False
):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    if course.creator_id == user.id:
        return course

    if require_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course creator can perform this action"
        )

    editor_result = await db.execute(
        select(CourseEditor).where(
            and_(
                CourseEditor.course_id == course_id,
                CourseEditor.user_id == user.id
            )
        )
    )
    editor = editor_result.scalar_one_or_none()

    if not editor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this course"
        )

    return course


async def create_course(data: CourseCreateRequest, creator: User, db: AsyncSession):
    course = Course(
        title=data.title, description=data.description,
        img_url=data.img_url, creator_id=creator.id
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)

    return course


async def get_my_courses(user: User, db: AsyncSession):
    creator_query = select(Course).where(Course.creator_id == user.id)
    editor_query = (
        select(Course)
        .join(CourseEditor, Course.id == CourseEditor.course_id)
        .where(CourseEditor.user_id == user.id)
    )

    creator_result = await db.execute(creator_query)
    editor_result = await db.execute(editor_query)

    created_courses = list(creator_result.scalars().all())
    editor_courses = list(editor_result.scalars().all())

    all_courses = {course.id: course for course in created_courses + editor_courses}

    return list(all_courses.values())


async def get_course_detail(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.modules))
        .where(Course.id == course_id)
    )
    course = result.scalar_one()
    course.modules.sort(key=lambda m: m.position)

    return course


async def update_course(
        course_id: int, data: CourseUpdateRequest,
        user: User, db: AsyncSession
):
    course = await check_course_access(course_id, user, db)

    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.img_url is not None:
        course.img_url = data.img_url

    await db.commit()
    await db.refresh(course)

    return course


async def delete_course(course_id: int, user: User, db: AsyncSession):
    course = await check_course_access(course_id, user, db, require_creator=True)
    await db.delete(course)
    await db.commit()


async def create_module(
        course_id: int, data: ModuleCreateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    module = Module(
        course_id=course_id,
        title=data.title,
        position=data.position
    )

    db.add(module)
    await db.commit()
    await db.refresh(module)

    return module


async def get_module_detail(module_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(Module)
        .options(
            selectinload(Module.materials)
            .selectinload(Material.material_files)
            .selectinload(MaterialFile.file)
        )
        .where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    await check_course_access(module.course_id, user, db)
    module.materials.sort(key=lambda mat: mat.position)
    for material in module.materials:
        material.files = material.material_files

    return module


async def update_module(
        module_id: int, data: ModuleUpdateRequest,
        user: User, db: AsyncSession
):
    result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    await check_course_access(module.course_id, user, db)

    if data.title is not None:
        module.title = data.title
    if data.position is not None:
        module.position = data.position

    await db.commit()
    await db.refresh(module)

    return module


async def delete_module(module_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    await check_course_access(module.course_id, user, db)

    await db.delete(module)
    await db.commit()


async def create_material(
        module_id: int, data: MaterialCreateRequest,
        user: User, db: AsyncSession
):
    result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    await check_course_access(module.course_id, user, db)

    material = Material(
        module_id=module_id,
        type=data.type,
        title=data.title,
        content_url=data.content_url,
        text_content=data.text_content,
        transcript=data.transcript,
        position=data.position
    )

    db.add(material)
    await db.commit()
    await db.refresh(material)

    return material


async def update_material(
        material_id: int, data: MaterialUpdateRequest,
        user: User, db: AsyncSession
):
    result = await db.execute(
        select(Material).join(Module).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    await check_course_access(material.module.course_id, user, db)

    if data.type is not None:
        material.type = data.type
    if data.title is not None:
        material.title = data.title
    if data.content_url is not None:
        material.content_url = data.content_url
    if data.text_content is not None:
        material.text_content = data.text_content
    if data.transcript is not None:
        material.transcript = data.transcript
    if data.position is not None:
        material.position = data.position

    await db.commit()
    await db.refresh(material)

    return material


async def delete_material(material_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(Material).join(Module).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    await check_course_access(material.module.course_id, user, db)

    await db.delete(material)
    await db.commit()


async def add_editor(course_id: int, teacher_id: int, user: User, db: AsyncSession):
    course = await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(User).where(User.id == teacher_id)
    )
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    role_result = await db.execute(
        select(Role).where(Role.id == teacher.role_id)
    )
    role = role_result.scalar_one()

    if role.name not in [RoleType.teacher, RoleType.admin]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a teacher or admin"
        )

    existing_editor = await db.execute(
        select(CourseEditor).where(
            and_(
                CourseEditor.course_id == course_id,
                CourseEditor.user_id == teacher_id
            )
        )
    )
    if existing_editor.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an editor of this course"
        )

    editor = CourseEditor(
        course_id=course_id,
        user_id=teacher_id,
        granted_by=user.id
    )

    db.add(editor)
    await db.commit()
    await db.refresh(editor)

    return editor


async def remove_editor(course_id: int, editor_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(CourseEditor).where(CourseEditor.id == editor_id)
    )
    editor = result.scalar_one_or_none()

    if not editor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editor not found"
        )

    await db.delete(editor)
    await db.commit()


async def attach_files_to_material(
        material_id: int, file_ids: List[int],
        user: User, db: AsyncSession
):
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.module))
        .where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    await check_course_access(material.module.course_id, user, db)

    result = await db.execute(
        select(File).where(File.id.in_(file_ids))
    )
    files = result.scalars().all()
    if len(files) != len(file_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some files not found"
        )

    material_files = []
    for file_id in file_ids:
        existing = await db.execute(
            select(MaterialFile).where(
                and_(
                    MaterialFile.material_id == material_id,
                    MaterialFile.file_id == file_id
                )
            )
        )
        if existing.scalar_one_or_none():
            continue
        material_file = MaterialFile(
            material_id=material_id,
            file_id=file_id
        )
        db.add(material_file)
        material_files.append(material_file)

    await db.commit()

    material_files_with_relations = []
    for mf in material_files:
        result = await db.execute(
            select(MaterialFile)
            .options(selectinload(MaterialFile.file))
            .options(selectinload(MaterialFile.material))
            .where(MaterialFile.id == mf.id)
        )
        mf_loaded = result.scalar_one()
        material_files_with_relations.append(mf_loaded)

    return material_files_with_relations


async def detach_file_from_material(
        material_id: int, file_id: int,
        user: User, db: AsyncSession
):
    result = await db.execute(
        select(Material).join(Module).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    await check_course_access(material.module.course_id, user, db)

    result = await db.execute(
        select(MaterialFile).where(
            and_(
                MaterialFile.material_id == material_id,
                MaterialFile.file_id == file_id
            )
        )
    )
    material_file = result.scalar_one_or_none()
    if not material_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not attached to this material"
        )

    await db.delete(material_file)
    await db.commit()
