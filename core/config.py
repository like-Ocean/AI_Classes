from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432

    # Application
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_RELOAD: bool = True
    APP_LOG_LEVEL: str = "debug"
    APP_PROTOCOL: str = "http"

    # Security (JWT)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [
        ".pdf", ".doc", ".docx", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
        ".mp4", ".webm", ".avi", ".mov", '.mp3', '.wav',
        ".zip", ".rar"
    ]

    # AI Service (DeepSeek через LiteLLM)
    # Timeweb Cloud AI (OpenAI-compatible)
    TIMEWEB_AGENT_ACCESS_ID: str  # agent_access_id
    TIMEWEB_API_KEY: str = ""  # Bearer token
    TIMEWEB_BASE_URL: str = "https://agent.timeweb.cloud"

    # AI Settings
    AI_TIMEOUT: int = 120
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.7

    # Ollama (для локальных моделей, если нужно)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    @property
    def TIMEWEB_FULL_BASE_URL(self) -> str:
        return f"{self.TIMEWEB_BASE_URL}/api/v1/cloud-ai/agents/{self.TIMEWEB_AGENT_ACCESS_ID}"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
