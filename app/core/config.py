from typing import List, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl, field_validator

class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str = "SaaS Backend"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "A professional SaaS backend with worker management"
    VERSION: str = "1.0.0"

    # Core Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")

    # Pinecone Vector DB
    PINECONE_API_KEY: Optional[str] = Field(None, env="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: Optional[str] = Field(None, env="PINECONE_INDEX_NAME")
    USE_PINECONE: bool = Field(False, env="USE_PINECONE")

    # AWS S3 Storage
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field("eu-central-1", env="AWS_REGION")
    AWS_S3_BUCKET: Optional[str] = Field(None, env="AWS_S3_BUCKET")
    USE_S3: bool = Field(False, env="USE_S3")

    # Local Storage Fallback
    UPLOAD_DIR: str = "uploads"
    CHROMA_DB_DIR: str = "chroma_db"
    
    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(None, env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")

    # Email (SMTP)
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: str = Field("noreply@saas.com", env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: str = Field("SaaS Platform", env="EMAILS_FROM_NAME")

    # Frontend (used in email links)
    FRONTEND_URL: str = Field("http://localhost:5173", env="FRONTEND_URL")

    # Logging & Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # THIS FIXES THE VALIDATION ERROR
    )

settings = Settings()
