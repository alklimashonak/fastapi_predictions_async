import logging
import pathlib
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.auth.base import BaseAuthRepository
from src.auth.models import User
from src.auth.repo import AuthRepository
from src.core.config import settings
from src.core.security import get_password_hash
from src.db.database import Base
from src.events.base import BaseEventRepository
from src.events.models import Event, Status
from src.events.repo import EventRepository
from src.matches.base import BaseMatchRepository
from src.matches.models import Match
from src.matches.repo import MatchRepository
from src.predictions.base import BasePredictionRepository
from src.predictions.models import Prediction
from src.predictions.repo import PredictionRepository

logger = logging.getLogger()

settings.TESTING = True

metadata = Base.metadata
async_engine = create_async_engine(settings.TEST_DATABASE_URL_POSTGRES)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture(scope='session')
def test_user() -> User:
    return User(
        id=uuid.uuid4(),
        email='test_user1@test.com',
        hashed_password=get_password_hash('1234'),
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture(scope='session')
def test_event() -> Event:
    return Event(
        id=123,
        name='Event',
        deadline=datetime.now(tz=timezone.utc),
        status=Status.not_started,
    )


@pytest.fixture(scope='session')
def test_match(test_event: Event) -> Match:
    return Match(
        id=123,
        home_team='Team 1',
        away_team='Team 2',
        start_time=datetime.now(tz=timezone.utc),
        event_id=test_event.id,
    )


@pytest.fixture(scope='session')
def another_match(test_event: Event) -> Match:
    return Match(
        id=124,
        home_team='Team 3',
        away_team='Team 4',
        start_time=datetime.now(tz=timezone.utc),
        event_id=test_event.id,
    )


@pytest.fixture(scope='session')
def test_prediction(test_user: User, test_match: Match) -> Prediction:
    return Prediction(
        id=123,
        home_goals=2,
        away_goals=2,
        match_id=test_match.id,
        user_id=test_user.id,
    )


@pytest.fixture(scope='session', autouse=True)
def run_migrations() -> None:
    root_dir = pathlib.Path(__file__).absolute().parent.parent.parent
    ini_file = root_dir.joinpath("alembic.ini").__str__()
    alembic_directory = root_dir.joinpath("alembic").__str__()
    config = Config(ini_file)
    config.set_main_option("script_location", alembic_directory)
    logger.info('RUN MIGRATIONS')
    command.upgrade(config, "head")
    yield
    logger.info('DROP MIGRATIONS')
    command.downgrade(config, 'base')


@pytest_asyncio.fixture(scope='session', autouse=True)
async def prepare_database(run_migrations: None) -> None:
    logger.info('PREPARE DATABASE')
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        logger.info('CREATE DB')
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        logger.info('DROP DB')


@pytest_asyncio.fixture(scope='session', autouse=True)
async def fill_db(
        prepare_database: None,
        test_user: User,
        test_event: Event,
        test_match: Match,
        test_prediction: Prediction,
        another_match: Match,
) -> None:
    async with async_session() as session:
        session.add(test_user)
        session.add(test_event)
        session.add(test_match)
        session.add(test_prediction)
        session.add(another_match)
        logger.info('CREATE TEST USER')
        logger.info('CREATE TEST EVENT')
        return await session.commit()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with async_engine.connect() as conn:
        await conn.begin()

        AsyncSessionLocal = async_sessionmaker(
            bind=conn,
            autocommit=False,
            autoflush=False,
            future=True,
            expire_on_commit=False)

        session = AsyncSessionLocal()

        yield session
        await session.close()
        await conn.rollback()


@pytest.fixture
def auth_repo(db_session: AsyncSession) -> BaseAuthRepository:
    yield AuthRepository(session=db_session)


@pytest.fixture
def event_repo(db_session: AsyncSession) -> BaseEventRepository:
    yield EventRepository(session=db_session)


@pytest.fixture
def match_repo(db_session: AsyncSession) -> BaseMatchRepository:
    yield MatchRepository(session=db_session)


@pytest.fixture
def prediction_repo(db_session: AsyncSession) -> BasePredictionRepository:
    yield PredictionRepository(session=db_session)
