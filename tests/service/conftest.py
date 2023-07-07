import contextlib
import logging
from datetime import datetime, timezone

import pytest_asyncio
from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.auth.base import BaseAuthService
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.auth.service import get_auth_service
from src.core.config import settings
from src.database import Base
from src.events.base import BaseEventService
from src.events.models import Event
from src.events.schemas import MatchCreate, EventCreate
from src.events.service import get_event_service

logger = logging.getLogger('tests')

metadata = Base.metadata
async_engine = create_async_engine(settings.TEST_DATABASE_URL_POSTGRES)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def override_get_db():
    async with async_session() as session:
        yield session


get_async_session_context = contextlib.asynccontextmanager(override_get_db)

get_auth_service_context = contextlib.asynccontextmanager(get_auth_service)
get_event_service_context = contextlib.asynccontextmanager(get_event_service)


@pytest_asyncio.fixture(scope='class', autouse=True)
async def prepare_database() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_auth_service_context(session) as auth_context:
                user = await auth_context.create(
                    UserCreate(email=EmailStr(email), password=password, is_superuser=is_superuser)
                )
                return user
    except UserAlreadyExists:
        logger.warning(f"User {email} already exists")


async def create_event(
        name: str,
        matches: list[MatchCreate]
) -> Event | None:
    async with get_async_session_context() as session:
        async with get_event_service_context(session) as event_context:
            event = EventCreate(
                name=name,
                deadline=datetime.now(tz=timezone.utc),
                matches=matches
            )
            return await event_context.create(event=event)


@pytest_asyncio.fixture
async def event_service() -> BaseEventService:
    async with get_async_session_context() as session:
        async with get_event_service_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def auth_service() -> BaseAuthService:
    async with get_async_session_context() as session:
        async with get_auth_service_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def test_event() -> Event:
    name = '1st event'
    matches = [
        MatchCreate(
            home_team='Aston Villa',
            away_team='Chelsea',
            start_time=datetime.now(tz=timezone.utc)
        )
    ]
    return await create_event(name=name, matches=matches)


@pytest_asyncio.fixture
async def test_user() -> User:
    email = settings.TEST_USER_EMAIL
    password = settings.TEST_USER_PASSWORD
    return await create_user(email=email, password=password, is_superuser=False)
