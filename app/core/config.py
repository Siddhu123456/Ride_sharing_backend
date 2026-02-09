from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SUPER_ADMIN_KEY: str
    UPLOAD_BASE : str = "uploads"

    class Config:
        env_file = ".env"

settings = Settings()
