from datetime import datetime

import pytest

from src import exceptions
from src.events.base import BaseEventService, BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import EventRead, EventCreate
from src.events.service import EventService
from tests.utils import EventModel, gen_matches


@pytest.fixture
def event_service(mock_event_repo: BaseEventRepository) -> BaseEventService:
    yield EventService(mock_event_repo)


@pytest.mark.asyncio
class TestGetMultiple:
    async def test_get_multiple_with_admin_mode(
            self,
            event_service: BaseEventService,
            created_event: EventModel,
            upcoming_event: EventModel,
    ) -> None:
        events = await event_service.get_multiple(admin_mode=True)

        assert EventRead.from_orm(created_event) in events
        assert EventRead.from_orm(upcoming_event) in events

    async def test_get_multiple_without_admin_mode(
            self,
            event_service: BaseEventService,
            created_event: EventModel,
            upcoming_event: EventModel,
    ) -> None:
        events = await event_service.get_multiple(admin_mode=False)

        assert EventRead.from_orm(created_event) not in events
        assert EventRead.from_orm(upcoming_event) in events


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_not_existing_event(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(exceptions.EventNotFound):
            await event_service.get_by_id(event_id=678)

    async def test_get_existing_event(
            self,
            event_service: BaseEventService,
            created_event: EventModel,
    ) -> None:
        event = await event_service.get_by_id(event_id=created_event.id)

        assert event == EventRead.from_orm(created_event)


@pytest.mark.asyncio
class TestCreateEvent:
    async def test_new_event_got_status_created(
            self,
            event_service: BaseEventService,
    ) -> None:
        event_data = EventCreate(
            name='new event',
            deadline=datetime.utcnow(),
        )

        event = await event_service.create(event=event_data)

        assert type(event) == EventRead
        assert event.status == EventStatus.created


@pytest.mark.asyncio
class TestUpgradeEventStatus:
    async def test_event_does_not_exist(self, event_service: BaseEventService) -> None:
        with pytest.raises(exceptions.EventNotFound):
            await event_service.upgrade_status(event_id=987)

    async def test_upgrade_completed_event(self, event_service: BaseEventService, completed_event: EventModel) -> None:
        with pytest.raises(exceptions.UnexpectedEventStatus):
            await event_service.upgrade_status(event_id=completed_event.id)

    async def test_upgrade_closed_event_that_has_uncompleted_matches(
            self, event_service: BaseEventService, closed_event: EventModel
    ) -> None:
        with pytest.raises(exceptions.MatchesAreNotFinished):
            await event_service.upgrade_status(event_id=closed_event.id)

    async def test_upgrade_created_event_without_matches(
            self, event_service: BaseEventService, created_event: EventModel,
    ) -> None:
        with pytest.raises(exceptions.TooFewMatches):
            await event_service.upgrade_status(event_id=created_event.id)

    async def test_upgrade_created_event_with_matches(
            self, event_service: BaseEventService, created_event: EventModel
    ) -> None:
        created_event.matches = gen_matches(event_id=created_event.id)

        event = await event_service.upgrade_status(event_id=created_event.id)

        assert type(event) == EventRead
        assert event.status == EventStatus.upcoming

    async def test_upgrade_upcoming_event(
            self, event_service: BaseEventService, upcoming_event: EventModel
    ) -> None:
        event = await event_service.upgrade_status(event_id=upcoming_event.id)

        assert type(event) == EventRead
        assert event.status == EventStatus.ongoing

    async def test_upgrade_ongoing_event(
            self, event_service: BaseEventService, ongoing_event: EventModel
    ) -> None:
        event = await event_service.upgrade_status(event_id=ongoing_event.id)

        assert type(event) == EventRead
        assert event.status == EventStatus.closed

    async def test_upgrade_closed_event_with_completed_matches(
            self, event_service: BaseEventService, ready_to_finish_event: EventModel
    ) -> None:
        event = await event_service.upgrade_status(event_id=ready_to_finish_event.id)

        assert type(event) == EventRead
        assert event.status == EventStatus.completed


@pytest.mark.asyncio
class TestDeleteEvent:
    async def test_delete_not_existing_event(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(exceptions.EventNotFound):
            await event_service.delete(event_id=987)
