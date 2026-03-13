from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "InsurBridge AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # AI / LLM
    GOOGLE_API_KEY: str | None = None

    # Security
    SECRET_KEY: str | None = None
    JWT_SECRET_KEY: str | None = None
    ENCRYPTION_KEY: str | None = None
    EXPOSE_ERROR_DETAILS: bool = False
    SQL_ECHO: bool = False
    AUTO_CREATE_TABLES: bool = False
    AUTO_SEED_DATA: bool = False

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "insurbridge"
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @property
    def jwt_secret_key(self) -> str:
        secret = self.JWT_SECRET_KEY or self.SECRET_KEY
        if not secret:
            raise RuntimeError("JWT secret key not configured. Set JWT_SECRET_KEY or SECRET_KEY.")
        return secret

    @property
    def encryption_key(self) -> str:
        if not self.ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY not configured. Set it before uploading or reading manuals.")
        return self.ENCRYPTION_KEY

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
