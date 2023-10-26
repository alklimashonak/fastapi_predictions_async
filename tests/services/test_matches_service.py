from datetime import datetime
from typing import Callable

import pytest
from fastapi import HTTPException

from src.matches.base import BaseMatchService
from src.matches.models import MatchStatus
from src.matches.schemas import MatchCreate
from src.matches.service import MatchService
from tests.utils import MatchModel, EventModel


@pytest.fixture
def match_service(
        mock_match_repo: Callable,
        mock_event_repo: Callable,
        upcoming_match: MatchModel,
        completed_match: MatchModel,
        created_event: EventModel,
        upcoming_event: EventModel,
) -> BaseMatchService:
    repo = mock_match_repo(matches=[upcoming_match, completed_match])
    event_repo = mock_event_repo(events=[created_event, upcoming_event])
    yield MatchService(repo, event_repo=event_repo)


@pytest.mark.asyncio
async def test_can_create_match(match_service: BaseMatchService, created_event: EventModel) -> None:
    match_data = MatchCreate(
        home_team='Roma',
        away_team='Juventus',
        start_time=datetime.utcnow(),
    )

    match = await match_service.create(match=match_data, event_id=created_event.id)

    assert hasattr(match, 'id')
    assert match.home_team == match_data.home_team
    assert match.away_team == match_data.away_team
    assert match.status == MatchStatus.upcoming
    assert match.start_time == match_data.start_time


@pytest.mark.asyncio
async def test_create_match_for_not_existed_event(match_service: BaseMatchService) -> None:
    match_data = MatchCreate(
        home_team='Roma',
        away_team='Juventus',
        start_time=datetime.utcnow(),
    )

    with pytest.raises(HTTPException):
        await match_service.create(match=match_data, event_id=43)


@pytest.mark.asyncio
async def test_create_for_upcoming_event_raises_exc(
        match_service: BaseMatchService,
        upcoming_event: EventModel
) -> None:
    match_data = MatchCreate(
        home_team='Roma',
        away_team='Juventus',
        start_time=datetime.utcnow(),
    )

    with pytest.raises(HTTPException):
        await match_service.create(match=match_data, event_id=upcoming_event.id)


@pytest.mark.asyncio
async def test_finish_upcoming_match_is_ok(match_service: BaseMatchService, upcoming_match: MatchModel) -> None:
    finished_match = await match_service.finish(match_id=upcoming_match.id, home_goals=3, away_goals=3)

    assert finished_match.id == upcoming_match.id
    assert finished_match.home_team == upcoming_match.home_team
    assert finished_match.away_team == upcoming_match.away_team
    assert finished_match.status == MatchStatus.completed
    assert finished_match.home_goals == 3
    assert finished_match.away_goals == 3


@pytest.mark.asyncio
async def test_finish_completed_match_raises_exc(match_service: BaseMatchService, completed_match: MatchModel) -> None:
    with pytest.raises(HTTPException):
        await match_service.finish(match_id=completed_match.id, home_goals=2, away_goals=2)


@pytest.mark.asyncio
async def test_delete_match_returns_none_if_exists(match_service: BaseMatchService, upcoming_match) -> None:
    match = await match_service.delete(match_id=upcoming_match.id)

    assert match is None


@pytest.mark.asyncio
async def test_delete_not_existed_match_raises_exc(match_service: BaseMatchService) -> None:
    with pytest.raises(HTTPException):
        await match_service.delete(match_id=9299)
