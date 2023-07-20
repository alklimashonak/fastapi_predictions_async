import contextlib
import logging
import pathlib
from datetime import datetime, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.auth.base import BaseAuthRepository
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.auth.dependencies import get_auth_repo
from src.core.config import settings
from src.db.database import Base
from src.events.base import BaseEventRepository
from src.events.models import Event
from src.events.schemas import MatchCreate, EventCreate
from src.events.dependencies import get_event_repo
from src.predictions.base import BasePredictionRepository
from src.predictions.dependencies import get_prediction_repo
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate

logger = logging.getLogger('tests')

settings.TESTING = True

metadata = Base.metadata
async_engine = create_async_engine(settings.TEST_DATABASE_URL_POSTGRES)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def override_get_db():
    async with async_session() as session:
        yield session


get_async_session_context = contextlib.asynccontextmanager(override_get_db)

get_auth_repo_context = contextlib.asynccontextmanager(get_auth_repo)
get_event_repo_context = contextlib.asynccontextmanager(get_event_repo)
get_prediction_repo_context = contextlib.asynccontextmanager(get_prediction_repo)


@pytest.fixture(scope='session', autouse=True)
def run_migrations() -> None:
    root_dir = pathlib.Path(__file__).absolute().parent.parent.parent
    ini_file = root_dir.joinpath("alembic.ini").__str__()
    alembic_directory = root_dir.joinpath("alembic").__str__()
    config = Config(ini_file)
    config.set_main_option("script_location", alembic_directory)
    command.upgrade(config, "head")


@pytest_asyncio.fixture(scope='function', autouse=True)
async def prepare_database() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_auth_repo_context(session) as auth_context:
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
        async with get_event_repo_context(session) as event_context:
            event = EventCreate(
                name=name,
                deadline=datetime.now(tz=timezone.utc),
                matches=matches
            )
            return await event_context.create(event=event)


async def create_prediction(
        prediction: PredictionCreate,
        user_id: UUID,
) -> Prediction:
    async with get_async_session_context() as session:
        async with get_prediction_repo_context(session) as prediction_context:
            return await prediction_context.create(prediction=prediction, user_id=user_id)


@pytest_asyncio.fixture
async def event_repo() -> BaseEventRepository:
    async with get_async_session_context() as session:
        async with get_event_repo_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def auth_repo() -> BaseAuthRepository:
    async with get_async_session_context() as session:
        async with get_auth_repo_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def prediction_repo() -> BasePredictionRepository:
    async with get_async_session_context() as session:
        async with get_prediction_repo_context(session) as db:
            yield db


@pytest_asyncio.fixture
async def test_event() -> Event:
    name = '1st event'
    matches = [
        MatchCreate(
            home_team='Aston Villa',
            away_team='Chelsea',
            start_time=datetime.now(tz=timezone.utc)
        ),
        MatchCreate(
            home_team='Liverpool',
            away_team='Newcastle',
            start_time=datetime.now(tz=timezone.utc)
        ),
    ]
    return await create_event(name=name, matches=matches)


@pytest_asyncio.fixture
async def test_user() -> User:
    email = settings.TEST_USER_EMAIL
    password = settings.TEST_USER_PASSWORD
    return await create_user(email=email, password=password, is_superuser=False)


@pytest_asyncio.fixture
async def test_prediction(test_user: User, test_event: Event) -> Prediction:
    match, _ = test_event.matches
    prediction = PredictionCreate(
        home_goals=2,
        away_goals=1,
        match_id=match.id,
    )

    return await create_prediction(prediction=prediction, user_id=test_user.id)
