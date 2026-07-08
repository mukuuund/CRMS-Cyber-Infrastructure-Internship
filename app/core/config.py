from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    DATABASE_URL: str

    @validator("DATABASE_URL", pre=True)
    def fix_postgres_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    class Config:
        env_file = ".env"

settings = Settings()
