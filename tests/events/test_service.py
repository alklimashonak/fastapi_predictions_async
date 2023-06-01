import datetime

import pytest

from src.events.models import Event
from src.events.schemas import EventUpdate, EventCreate, MatchCreate, EventSchema
from src.events.service import EventDatabase


@pytest.mark.asyncio
async def test_get_event_by_id_returns_event(test_event: Event, event_db: EventDatabase) -> None:
    event = await event_db.get_event_by_id(event_id=test_event.id)

    assert event.id == test_event.id


@pytest.mark.asyncio
async def test_can_create_event(event_db: EventDatabase) -> None:
    event_name = 'my new event'
    data = EventCreate(
        name=event_name,
        start_time=datetime.datetime.utcnow()
    )

    new_event = await event_db.create_event(event=data)

    assert new_event.name == event_name


@pytest.mark.asyncio
async def test_can_create_event_with_match(event_db: EventDatabase) -> None:
    event_name = 'event'
    matches = [
        MatchCreate(
            team1='1st team',
            team2='2nd team',
            start_time=datetime.datetime.utcnow()
        )
    ]

    data = EventCreate(
        name=event_name,
        start_time=datetime.datetime.utcnow(),
        matches=matches
    )

    event = await event_db.create_event(event=data)

    assert len(event.matches) == 1


@pytest.mark.asyncio
async def test_can_update_event_name(test_event: Event, event_db: EventDatabase) -> None:
    data = EventUpdate(
        name='new event',
        start_time=datetime.datetime.utcnow()
    )

    updated_event = await event_db.update_event(event_id=test_event.id, updated_event=data)

    assert test_event.name == '1st event'
    assert updated_event.name == 'new event'
    assert test_event.matches.pop().id == updated_event.matches.pop().id


@pytest.mark.asyncio
async def test_can_create_match(test_event: EventSchema, event_db: EventDatabase) -> None:
    data = MatchCreate(
        team1='1st team',
        team2='2nd team',
        status=0,
        start_time=datetime.datetime.utcnow()
    )

    await event_db._create_match(match=data, event_id=test_event.id)

    event_after = await event_db.get_event_by_id(event_id=test_event.id)

    matches_before = len(test_event.matches)
    matches_after = len(event_after.matches)

    assert matches_before + 1 == matches_after


@pytest.mark.asyncio
async def test_can_delete_match(test_event: Event, event_db: EventDatabase) -> None:
    await event_db._delete_match(match_id=test_event.matches[0].id)

    event_after = await event_db.get_event_by_id(event_id=test_event.id)

    matches_before = len(test_event.matches)
    matches_after = len(event_after.matches)

    assert matches_before == matches_after + 1
