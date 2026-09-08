from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql://sentry:sentry_dev_pw@localhost:5432/sentry_router"

    class Config:
        env_file = ".env"

settings = Settings()