from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from src.events.base import BaseEventRepository, BaseEventService
from src.events.models import Status
from src.events.schemas import EventCreate, MatchCreate
from src.events.service import EventService
from tests.services.conftest import EventModel
from tests.utils import gen_matches


@pytest.fixture
def event_service(mock_event_repo: BaseEventRepository) -> BaseEventService:
    yield EventService(mock_event_repo)


@pytest.mark.asyncio
class TestGetMultiple:
    async def test_get_multiple_events_works(self, event_service: BaseEventService) -> None:
        users = await event_service.get_multiple()

        assert len(users) == 1


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
        assert event.matches == event1.matches

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
            matches=[],
        )

        event = await event_service.create(event=new_event)

        assert hasattr(event, 'id')
        assert event.name == new_event.name
        assert event.status == Status.not_started
        assert event.deadline == new_event.deadline
        assert event.matches == new_event.matches

    async def test_create_valid_data_with_matches_works(
            self,
            event_service: BaseEventService,
    ) -> None:
        new_event = EventCreate(
            name='new event',
            deadline=datetime.utcnow(),
            matches=[
                MatchCreate(
                    home_team='Eve',
                    away_team='Not',
                    start_time=datetime.utcnow(),
                )
            ],
        )

        event = await event_service.create(event=new_event)

        assert hasattr(event, 'id')
        assert event.name == new_event.name
        assert event.status == Status.not_started
        assert event.deadline == new_event.deadline
        assert len(event.matches) == len(new_event.matches)


@pytest.mark.asyncio
class TestUpdate:
    async def test_run_not_existed_event_raises_err(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(HTTPException):
            await event_service.run(event_id=99213)

    async def test_run_event_in_progress_raises_err(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        event1.status = Status.in_process

        with pytest.raises(HTTPException):
            await event_service.run(event_id=event1.id)

        event1.status = Status.not_started

    async def test_run_without_5_matches_raises_err(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        assert event1.status == Status.not_started

        with pytest.raises(HTTPException):
            await event_service.run(event_id=event1.id)

    async def test_run_correctly_event_returns_event(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        default_matches = event1.matches
        event1.matches = gen_matches(event_id=event1.id, count=5)

        updated_event = await event_service.run(event_id=event1.id)

        assert updated_event.status == Status.in_process

        event1.status = Status.not_started
        event1.matches = default_matches


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


@pytest.mark.asyncio
class TestCreateMatch:
    async def test_create_valid_data_works(self, event_service: BaseEventService, event1: EventModel) -> None:
        home_team = 'Everton'
        away_team = 'Bayern'
        start_time = datetime.now(tz=timezone.utc)

        new_match = MatchCreate(
            home_team=home_team,
            away_team=away_team,
            start_time=start_time,
        )

        match = await event_service.create_match(match=new_match, event_id=event1.id)

        assert hasattr(match, 'id')
        assert match.status == Status.not_started
        assert match.home_team == home_team
        assert match.away_team == away_team
        assert match.home_goals is None
        assert match.away_goals is None
        assert match.start_time == start_time


@pytest.mark.asyncio
class TestDeleteMatch:
    async def test_delete_match_returns_none_if_event_exists(
            self,
            event_service: BaseEventService,
            event1: EventModel,
    ) -> None:
        deleted_event = await event_service.delete_match_by_id(match_id=event1.matches[0].id)

        assert not deleted_event

    async def test_delete_match_not_existed_event_raises_exc(
            self,
            event_service: BaseEventService,
    ) -> None:
        with pytest.raises(HTTPException):
            await event_service.delete_match_by_id(match_id=9299)
