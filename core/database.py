import os
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
    f"/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENV") == "development",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    future=True
)

Base = declarative_base()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
