from datetime import datetime
from datetime import timezone

import pytest

from src.events.base import BaseEventService
from src.events.models import Status, Event
from src.events.schemas import EventCreate, MatchCreate


@pytest.mark.asyncio
async def test_get_event_by_id_returns_event(test_event: Event, event_service: BaseEventService) -> None:
    event = await event_service.get_by_id(event_id=test_event.id)

    assert event.id == test_event.id
    assert event.name == test_event.name
    assert event.status == test_event.status
    assert event.deadline == test_event.deadline


@pytest.mark.asyncio
async def test_create_event_works(event_service: BaseEventService) -> None:
    data = EventCreate(
        name='my 1st event',
        deadline=datetime.now(tz=timezone.utc)
    )

    new_event = await event_service.create(event=data)

    assert new_event.name == data.name
    assert new_event.deadline == data.deadline


@pytest.mark.asyncio
async def test_delete_event_works(test_event: Event, event_service: BaseEventService) -> None:
    event = await event_service.get_by_id(event_id=test_event.id)
    assert event

    await event_service.delete(event_id=test_event.id)

    deleted_event = await event_service.get_by_id(event_id=test_event.id)

    assert not deleted_event


@pytest.mark.asyncio
async def test_create_matches_works(test_event: Event, event_service: BaseEventService) -> None:
    team1 = '1st team'
    team2 = '2nd team'
    start_time = datetime.now(tz=timezone.utc)

    data = [
        MatchCreate(
            home_team=team1,
            away_team=team2,
            start_time=start_time,
        ),
        MatchCreate(
            home_team=team1,
            away_team=team2,
            start_time=start_time,
        )
    ]

    await event_service._create_matches(matches=data, event_id=test_event.id)
    refreshed_event = await event_service.get_by_id(event_id=test_event.id)

    assert len(refreshed_event.matches) == len(test_event.matches) + 2
