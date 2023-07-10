from functools import lru_cache
from typing import TYPE_CHECKING

from pydantic import BaseSettings, PostgresDsn

if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


class Settings(BaseSettings):
    TESTING: bool = False

    SECRET_KEY: str = 'secret'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL_SQLITE: str = 'sqlite+aiosqlite:///./predictions.db'
    TEST_DATABASE_URL_SQLITE: str = "sqlite+aiosqlite:///./predictions_test.db"

    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = '5741'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: str = '5432'
    POSTGRES_DB: str = 'predictions'

    TEST_POSTGRES_DB: str = 'predictions_test'

    DATABASE_URL_POSTGRES: PostgresDsn = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            path=f"/{POSTGRES_DB or ''}",
        )

    TEST_DATABASE_URL_POSTGRES: PostgresDsn = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            path=f"/{TEST_POSTGRES_DB or ''}",
        )

    TEST_USER_EMAIL: EmailStr = 'testuser@example.com'
    TEST_USER_PASSWORD: str = '1234'

    class Config:
        env_file = '.env'


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
