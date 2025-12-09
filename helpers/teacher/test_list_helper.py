from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from models import Test, Material, Module
from typing import List


async def load_module_tests(course_id: int, module_id: int, db: AsyncSession) -> List[Test]:
    result = await db.execute(
        select(Test)
        .join(Material, Test.material_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .options(
            selectinload(Test.material).selectinload(Material.module),
            selectinload(Test.questions)
        )
        .where(
            and_(
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
        .order_by(Material.position, Test.id)
    )
    return list(result.scalars().all())


async def load_material_tests(
    course_id: int, module_id: int,
    material_id: int, db: AsyncSession
) -> List[Test]:
    result = await db.execute(
        select(Test)
        .join(Material, Test.material_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .options(selectinload(Test.questions))
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
        .order_by(Test.id)
    )
    return list(result.scalars().all())
