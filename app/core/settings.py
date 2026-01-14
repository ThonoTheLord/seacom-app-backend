from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DB_HOST: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: int = 0
    DB_NAME: str = ""

    # Security
    JWT_TOKEN_EXPIRE_MINUTES: int = 0
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 0
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:5173")

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT_SECRET_KEY is set and has minimum length."""
        if not v or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be set and at least 32 characters long. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @property
    def allowed_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        """"""
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )
    
    class Config:
        env_file = ".env"


app_settings = AppSettings()
