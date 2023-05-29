import asyncio
import contextlib
import logging

import pytest
import pytest_asyncio
from fastapi_users.exceptions import UserAlreadyExists
from httpx import AsyncClient
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.auth.dependencies import get_user_db
from src.auth.manager import get_user_manager
from src.auth.schemas import UserCreate
from src.config import settings
from src.database import get_async_session
from src.main import app
from src.auth.models import User

logger = logging.getLogger('tests')

metadata = User.metadata

SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL_POSTGRES

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def override_get_db():
    async with async_session() as session:
        yield session


app.dependency_overrides[get_async_session] = override_get_db

get_async_session_context = contextlib.asynccontextmanager(override_get_db)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def get_user_manager():
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    return user_manager
    except Exception:
        logger.warning('Something wrong to get manager')


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=EmailStr(email), password=password, is_superuser=is_superuser
                        )
                    )
                    return user
    except UserAlreadyExists:
        logger.warning(f"User {email} already exists")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='class', autouse=True)
async def prepare_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        pass
        #await conn.run_sync(metadata.drop_all)


@pytest_asyncio.fixture(scope='function')
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope='class')
async def manager():
    user_manager = await get_user_manager()
    return user_manager


@pytest_asyncio.fixture(scope='class')
async def test_user() -> User:
    user = await create_user(email=settings.TEST_USER_EMAIL, password=settings.TEST_USER_PASSWORD)
    return user
