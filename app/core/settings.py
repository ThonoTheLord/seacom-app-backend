from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """"""

    # Database
    DB_HOST: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: int = 0
    DB_NAME: str = ""

    # Security
    JWT_TOKEN_EXPIRE_MINUTES: int = 0
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 0
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITH: str = ""

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
