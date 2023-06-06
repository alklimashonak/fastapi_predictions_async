from datetime import datetime

import pytest

from src.events.models import EP, EventStatus, MatchStatus
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
async def test_can_create_event(event_db: EventDatabase) -> None:
    data = EventCreate(
        name='my 1st event',
        status=EventStatus.not_started,
        start_time=datetime.utcnow()
    )

    new_event = await event_db.create_event(event=data)

    assert new_event.name == data.name


@pytest.mark.asyncio
async def test_can_update_event_data(test_event: EP, event_db: EventDatabase) -> None:
    new_name = 'new event'
    new_start_time = datetime.utcnow()

    data = EventUpdate(
        name=new_name,
        start_time=new_start_time
    )

    updated_event = await event_db.update_event(event_id=test_event.id, event=data)

    assert updated_event.name == new_name
    assert test_event.name != updated_event.name


@pytest.mark.asyncio
async def test_can_delete_event(test_event: EP, event_db: EventDatabase) -> None:
    await event_db.delete_event(event_id=test_event.id)

    deleted_event = await event_db.get_event_by_id(event_id=test_event.id)

    assert not deleted_event


@pytest.mark.asyncio
async def test_can_create_match(test_event: EP, event_db: EventDatabase) -> None:
    team1 = '1st team'
    team2 = '2nd team'
    start_time = datetime.utcnow()

    data = MatchCreate(
        team1=team1,
        team2=team2,
        start_time=start_time
    )

    match = await event_db._create_match(match=data, event_id=test_event.id)

    assert match.team1 == team1
    assert match.team2 == team2


@pytest.mark.asyncio
async def test_can_update_match(test_event: EP, event_db: EventDatabase) -> None:
    data = MatchCreate(
        team1='team1',
        team2='team2',
        start_time=datetime.utcnow()
    )
    match = await event_db._create_match(match=data, event_id=test_event.id)

    updated_data = MatchUpdate(
        id=match.id,
        team1='new team 1',
        team2='new team 2',
        start_time=datetime.utcnow()
    )

    updated_match = await event_db._update_match(match=updated_data)

    assert updated_match.team1 == 'new team 1'
    assert updated_match.team2 == 'new team 2'


@pytest.mark.asyncio
async def test_can_delete_match(test_event: EP, event_db: EventDatabase) -> None:
    await event_db._delete_match(match_id=test_event.matches[0].id)

    event_after = await event_db.get_event_by_id(event_id=test_event.id)

    matches_before = len(test_event.matches)
    matches_after = len(event_after.matches)

    assert matches_before == matches_after + 1
