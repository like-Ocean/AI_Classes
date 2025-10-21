from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from core.database import engine, Base
# from routers import routes
# from init_db import init_db



load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("ENV") == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # await init_db()

    yield
    await engine.dispose()


app = FastAPI(
    title="Education Reviews Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# for router in routes:
#     app.include_router(router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST"),
        port=int(os.getenv("APP_PORT")),
        reload=os.getenv("APP_RELOAD", "False").lower() == "true",
        log_level=os.getenv("APP_LOG_LEVEL", "info").lower()
    )
