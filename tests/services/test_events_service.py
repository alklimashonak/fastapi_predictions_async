from datetime import datetime
from typing import Callable

import pytest
from fastapi import HTTPException

from src.events.base import BaseEventService
from src.events.models import EventStatus
from src.events.schemas import EventCreate
from src.events.service import EventService
from tests.utils import EventModel, gen_matches


@pytest.fixture
def event_service(mock_event_repo: Callable, event1: EventModel) -> BaseEventService:
    repo = mock_event_repo(events=[event1])
    yield EventService(repo)


@pytest.mark.asyncio
class TestGetMultiple:
    async def test_get_multiple_events_works(self, event_service: BaseEventService) -> None:
        events = await event_service.get_multiple(admin_mode=False)

        assert len(events) == 1


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_existent_event_returns_event(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        event = await event_service.get_by_id(event_id=event1.id)

        assert event.id == event1.id
        assert event.name == event1.name
        assert event.status == event1.status
        assert len(event.matches) == len(event1.matches)

    async def test_get_not_existent_event_raises_http_exc(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(HTTPException):
            await event_service.get_by_id(event_id=99213)


@pytest.mark.asyncio
class TestCreate:
    async def test_create_valid_data_works(
            self,
            event_service: BaseEventService,
    ) -> None:
        new_event = EventCreate(
            name='new event',
            deadline=datetime.utcnow(),
        )

        event = await event_service.create(event=new_event)

        assert hasattr(event, 'id')
        assert event.name == new_event.name
        assert event.status == EventStatus.created
        assert event.deadline == new_event.deadline


@pytest.mark.asyncio
class TestUpdate:
    async def test_run_not_existed_event_raises_err(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(HTTPException):
            await event_service.run(event_id=99213)

    async def test_run_ongoing_event_raises_err(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        event1.status = EventStatus.ongoing

        with pytest.raises(HTTPException):
            await event_service.run(event_id=event1.id)

        event1.status = EventStatus.created

    async def test_run_without_5_matches_raises_err(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        assert event1.status == EventStatus.created

        with pytest.raises(HTTPException):
            await event_service.run(event_id=event1.id)

    async def test_run_created_event_returns_event(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        event1.matches = gen_matches(event_id=event1.id, count=5)

        updated_event = await event_service.run(event_id=event1.id)

        assert updated_event.status == EventStatus.ongoing


@pytest.mark.asyncio
class TestDelete:
    async def test_delete_returns_none_if_event_exists(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        deleted_event = await event_service.delete(event_id=event1.id)

        assert not deleted_event

    async def test_delete_not_existed_event_raises_exc(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(HTTPException):
            await event_service.delete(event_id=9299)
