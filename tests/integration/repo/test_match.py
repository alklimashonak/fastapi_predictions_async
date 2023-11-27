from datetime import datetime, timezone

import pytest

from src.events.models import Event
from src.matches.base import BaseMatchRepository
from src.matches.models import Match, MatchStatus
from src.matches.schemas import MatchCreate, MatchUpdate


@pytest.mark.asyncio
async def test_get_match_by_id(
        match_repo: BaseMatchRepository,
        test_match: Match,
) -> None:
    db_match = await match_repo.get_by_id(match_id=test_match.id)

    assert db_match.id == test_match.id
    assert db_match.home_team == test_match.home_team
    assert db_match.away_team == test_match.away_team
    assert db_match.start_time == test_match.start_time
    assert db_match.status == MatchStatus.upcoming
    assert db_match.event_id == test_match.event_id


@pytest.mark.asyncio
async def test_create_match(match_repo: BaseMatchRepository, test_event: Event) -> None:
    match = MatchCreate(
        home_team='Team 3',
        away_team='Team 4',
        start_time=datetime.now(tz=timezone.utc),
    )

    db_match = await match_repo.create(match=match, event_id=test_event.id)

    assert db_match.id
    assert db_match.home_team == match.home_team
    assert db_match.away_team == match.away_team
    assert db_match.start_time == match.start_time
    assert db_match.status == MatchStatus.upcoming
    assert db_match.event_id == test_event.id


@pytest.mark.asyncio
async def test_update_match(match_repo: BaseMatchRepository, test_match: Match) -> None:
    data = MatchUpdate(
        home_team=test_match.home_team,
        away_team=test_match.away_team,
        start_time=test_match.start_time,
        home_goals=test_match.home_goals,
        away_goals=test_match.away_goals,
        status=MatchStatus.completed,
    )

    updated_match = await match_repo.update(match_id=test_match.id, match=data)

    assert updated_match.id == test_match.id
    assert updated_match.status == MatchStatus.completed


@pytest.mark.asyncio
async def test_delete_match(match_repo: BaseMatchRepository, test_match: Match) -> None:
    await match_repo.delete(match_id=test_match.id)

    deleted_match = await match_repo.get_by_id(match_id=test_match.id)

    assert not deleted_match
