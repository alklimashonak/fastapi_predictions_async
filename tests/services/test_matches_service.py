from datetime import datetime, timezone
from typing import Callable

import pytest
from fastapi import HTTPException

from src.matches.base import BaseMatchService
from src.matches.models import Status
from src.matches.schemas import MatchCreate
from src.matches.service import MatchService
from tests.services.utils import MatchModel, EventModel


@pytest.fixture
def match_service(mock_match_repo: Callable, match1: MatchModel) -> BaseMatchService:
    repo = mock_match_repo(matches=[match1])
    yield MatchService(repo)


@pytest.mark.asyncio
async def test_can_create_match(match_service: BaseMatchService, event1: EventModel) -> None:
    match_data = MatchCreate(
        home_team='Roma',
        away_team='Juventus',
        start_time=datetime.utcnow(),
    )

    match = await match_service.create(match=match_data, event_id=event1.id)

    assert hasattr(match, 'id')
    assert match.home_team == match_data.home_team
    assert match.away_team == match_data.away_team
    assert match.status == Status.not_started
    assert match.start_time == match_data.start_time


@pytest.mark.asyncio
async def test_delete_match_returns_none_if_exists(match_service: BaseMatchService, match1) -> None:
    match = await match_service.delete(match_id=match1.id)

    assert match is None


@pytest.mark.asyncio
async def test_delete_not_existed_match_raises_exc(match_service: BaseMatchService) -> None:
    with pytest.raises(HTTPException):
        await match_service.delete(match_id=9299)
