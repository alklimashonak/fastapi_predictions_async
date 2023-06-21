import contextlib
import logging
from datetime import datetime, timezone

import pytest_asyncio
from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.auth.dependencies import get_user_db
from src.auth.manager import get_user_manager
from src.auth.schemas import UserCreate
from src.config import settings
from src.database import Base
from src.events.base import BaseEventDatabase
from src.events.dependencies import get_event_db
from src.events.models import MatchStatus, Event
from src.events.schemas import MatchCreate, EventCreate

logger = logging.getLogger('tests')


metadata = Base.metadata
async_engine = create_async_engine(settings.TEST_DATABASE_URL_POSTGRES)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def override_get_db():
    async with async_session() as session:
        yield session


get_async_session_context = contextlib.asynccontextmanager(override_get_db)

get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)

get_event_db_context = contextlib.asynccontextmanager(get_event_db)


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


async def create_event(
        name: str,
        matches: list[MatchCreate]
) -> Event | None:
    async with get_async_session_context() as session:
        async with get_event_db_context(session) as db:
            event = EventCreate(
                name=name,
                start_time=datetime.now(tz=timezone.utc),
                matches=matches
            )
            return await db.create_event(event=event)


@pytest_asyncio.fixture
async def event_db() -> BaseEventDatabase:
    async with get_async_session_context() as session:
        async with get_event_db_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def test_event() -> Event:
    name = '1st event'
    matches = [
        MatchCreate(
            team1='Aston Villa',
            team2='Chelsea',
            status=MatchStatus.not_started,
            start_time=datetime.now(tz=timezone.utc)
        )
    ]
    return await create_event(name=name, matches=matches)
