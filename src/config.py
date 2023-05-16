from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_AUTH = 'secret'

    DATABASE_URL = 'sqlite+aiosqlite:///./predictions.db'
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./predictions_test.db"

    TEST_USER_EMAIL = 'testuser@example.com'
    TEST_USER_PASSWORD = '1234'

    class Config:
        env_file = '.env'


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
