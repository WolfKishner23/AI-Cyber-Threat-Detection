from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Cyber Threat Investigation & Response Platform"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database connection string.
    # Note: we use SQLite by default. When using SQLite, we also configure uvicorn/SQLAlchemy threads properly.
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./cyber_threat_platform.db"

    # CORS configuration (useful for future web frontend connection)
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
