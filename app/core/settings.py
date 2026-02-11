from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DB_HOST: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: int = 5432
    DB_NAME: str = ""

    # Supabase Storage
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "attachments"

    # Security
    JWT_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:5173")

    # Presence backend (db | redis). If 'redis' and REDIS_URL is set, presence uses Redis for heartbeats.
    PRESENCE_BACKEND: str = Field(default="db", description="Storage for presence: 'db' or 'redis'")
    REDIS_URL: str | None = Field(default=None, description="Optional Redis URL for presence/pubsub (e.g. redis://host:6379/0)")
    PRESENCE_REDIS_TTL_SECONDS: int = Field(default=300, description="How long (s) a heartbeat is considered valid in Redis")
    PRESENCE_PUBSUB_CHANNEL: str = Field(default="presence_events", description="Redis pubsub channel for presence events")
    PRESENCE_REDIS_CONNECT_TIMEOUT_SECONDS: int = Field(
        default=5,
        description="Redis connect timeout (seconds) for presence operations",
    )
    PRESENCE_REDIS_SOCKET_TIMEOUT_SECONDS: int = Field(
        default=5,
        description="Redis command socket timeout (seconds) for presence operations",
    )

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
