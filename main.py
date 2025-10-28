import os
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.database import engine, Base
from core.config import settings
from core.init_db import init_database
from routers import routes


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV == "development" or settings.ENV == "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")

    try:
        await init_database()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        if settings.ENV == "production":
            raise

    print("Application started successfully")

    yield

    await engine.dispose()


app = FastAPI(
    title="Education Reviews Platform",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in routes:
    app.include_router(router, prefix="/api")

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.APP_LOG_LEVEL.lower()
    )
