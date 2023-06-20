from datetime import datetime
from datetime import timezone

import pytest

from src.events.models import EP, EventStatus
from src.events.schemas import EventUpdate, EventCreate, MatchCreate, MatchUpdate
from src.events.service import EventDatabase


@pytest.mark.asyncio
async def test_get_event_by_id_returns_event(test_event: EP, event_db: EventDatabase) -> None:
    event = await event_db.get_event_by_id(event_id=test_event.id)

    assert event.id == test_event.id
    assert event.name == test_event.name
    assert event.status == test_event.status
    assert event.start_time == test_event.start_time


@pytest.mark.asyncio
async def test_create_event_works(event_db: EventDatabase) -> None:
    data = EventCreate(
        name='my 1st event',
        status=EventStatus.not_started,
        start_time=datetime.now(tz=timezone.utc)
    )

    new_event = await event_db.create_event(event=data)

    assert new_event.name == data.name
    assert new_event.start_time == data.start_time


@pytest.mark.asyncio
async def test_update_events_works(test_event: EP, event_db: EventDatabase) -> None:
    new_name = 'new event'
    new_start_time = datetime.now(tz=timezone.utc)

    data = EventUpdate(
        name=new_name,
        start_time=new_start_time
    )

    updated_event = await event_db.update_event(event_id=test_event.id, event=data)

    assert updated_event.name == new_name
    assert test_event.name != updated_event.name


@pytest.mark.asyncio
async def test_delete_event_works(test_event: EP, event_db: EventDatabase) -> None:
    event = await event_db.get_event_by_id(event_id=test_event.id)
    assert event

    await event_db.delete_event(event_id=test_event.id)

    deleted_event = await event_db.get_event_by_id(event_id=test_event.id)

    assert not deleted_event


@pytest.mark.asyncio
async def test_create_match_works(test_event: EP, event_db: EventDatabase) -> None:
    team1 = '1st team'
    team2 = '2nd team'
    start_time = datetime.now(tz=timezone.utc)

    data = MatchCreate(
        team1=team1,
        team2=team2,
        start_time=start_time
    )

    await event_db._create_match(match=data, event_id=test_event.id)
    refreshed_event = await event_db.get_event_by_id(event_id=test_event.id)

    assert len(refreshed_event.matches) == len(test_event.matches) + 1


@pytest.mark.asyncio
async def test_update_match_works(test_event: EP, event_db: EventDatabase) -> None:
    match = test_event.matches[0]

    new_team1 = 'new team 1'
    new_team2 = 'new team 2'

    updated_data = MatchUpdate(
        id=match.id,
        team1=new_team1,
        team2=new_team2,
        start_time=datetime.now(tz=timezone.utc)
    )

    await event_db._update_match(match=updated_data)

    refreshed_event = await event_db.get_event_by_id(event_id=test_event.id)
    updated_match = refreshed_event.matches[0]

    assert updated_match.team1 == new_team1
    assert updated_match.team2 == new_team2


@pytest.mark.asyncio
async def test_delete_match_works(test_event: EP, event_db: EventDatabase) -> None:
    assert len(test_event.matches) > 0

    await event_db._delete_match(match_id=test_event.matches[0].id)

    event_after = await event_db.get_event_by_id(event_id=test_event.id)

    matches_before = len(test_event.matches)
    matches_after = len(event_after.matches)

    assert matches_before == matches_after + 1
