from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "ERP 进销存系统"
    # 开发环境默认 SQLite，生产切换为 MySQL：
    # DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/erp?charset=utf8mb4
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./erp.db"
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me-in-prod")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    ALLOW_NEGATIVE_STOCK: bool = os.getenv("ALLOW_NEGATIVE_STOCK", "false").lower() == "true"

    class Config:
        env_file = ".env"


settings = Settings()
