from datetime import datetime

import pytest_asyncio

from src.events.schemas import MatchCreate
from tests.conftest import get_async_session_context
from tests.events.utils import create_event, get_event_db_context


@pytest_asyncio.fixture
async def event_db():
    async with get_async_session_context() as session:
        async with get_event_db_context(session) as db:
            yield db


@pytest_asyncio.fixture(scope='function')
async def test_event():
    name = '1st event'
    matches = [
        MatchCreate(
            team1='Aston Villa',
            team2='Chelsea',
            status=0,
            start_time=datetime.utcnow()
        )
    ]
    return await create_event(name=name, matches=matches)
