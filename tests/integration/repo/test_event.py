from datetime import datetime, timezone

import pytest

from src.events.base import BaseEventRepository
from src.events.models import Event, EventStatus
from src.events.schemas import EventCreate, EventUpdate


@pytest.mark.asyncio
class TestGet:
    async def test_get_event_by_id(self, event_repo: BaseEventRepository, test_event: Event) -> None:
        event = await event_repo.get_by_id(event_id=test_event.id)

        assert event.id == test_event.id
        assert event.name == test_event.name
        assert event.deadline == test_event.deadline
        assert event.status == test_event.status

    async def test_event_does_not_exist(self, event_repo: BaseEventRepository) -> None:
        db_event = await event_repo.get_by_id(event_id=999)

        assert not db_event


@pytest.mark.asyncio
class TestCreate:
    async def test_create_event(self, event_repo: BaseEventRepository) -> None:
        event = EventCreate(
            name='New Event',
            deadline=datetime.now(tz=timezone.utc),
        )

        db_event = await event_repo.create(event=event)

        assert db_event.id
        assert db_event.name == event.name
        assert db_event.status == EventStatus.created
        assert db_event.deadline == event.deadline
        assert db_event.matches == []


@pytest.mark.asyncio
class TestUpdate:
    async def test_run_event(self, event_repo: BaseEventRepository, test_event: Event) -> None:
        assert test_event.status == EventStatus.created

        event = EventUpdate(name=test_event.name, deadline=test_event.deadline, status=EventStatus.upcoming)

        updated_event = await event_repo.update(event_id=test_event.id, event=event)

        assert updated_event.status == EventStatus.upcoming


@pytest.mark.asyncio
class TestDelete:
    async def test_delete_event(self, event_repo: BaseEventRepository, test_event: Event) -> None:
        await event_repo.delete(event_id=test_event.id)

        deleted_event = await event_repo.get_by_id(event_id=test_event.id)

        assert not deleted_event


@pytest.mark.asyncio
async def test_get_multiple(event_repo: BaseEventRepository) -> None:
    events = await event_repo.get_multiple(admin_mode=True)

    assert len(events) == 1
