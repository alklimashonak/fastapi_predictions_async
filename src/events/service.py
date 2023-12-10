from typing import Sequence

from src import exceptions
from src.events.base import BaseEventService, BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import EventCreate, EventRead, EventUpdate
from src.matches.models import MatchStatus


class EventService(BaseEventService):
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    async def get_multiple(self, admin_mode: bool = False, offset: int = 0, limit: int = 100) -> Sequence[EventRead]:
        events = await self.repo.get_multiple(admin_mode=admin_mode, offset=offset, limit=limit)
        return [EventRead.from_orm(event) for event in events]

    async def get_by_id(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        return EventRead.from_orm(event)

    async def create(self, event: EventCreate) -> EventRead:
        new_event = await self.repo.create(event=event)

        return EventRead.from_orm(new_event)

    async def run(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status != EventStatus.created:
            raise exceptions.UnexpectedEventStatus

        if len(event.matches) != 5:
            raise exceptions.TooFewMatches

        event = EventUpdate(name=event.name, deadline=event.deadline, status=EventStatus.upcoming)

        updated_event = await self.repo.update(event_id=event_id, event=event)

        return EventRead.from_orm(updated_event)

    async def start(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status != EventStatus.upcoming:
            raise exceptions.UnexpectedEventStatus

        event = EventUpdate(name=event.name, deadline=event.deadline, status=EventStatus.ongoing)

        updated_event = await self.repo.update(event_id=event_id, event=event)

        return EventRead.from_orm(updated_event)

    async def close(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status != EventStatus.ongoing:
            raise exceptions.UnexpectedEventStatus

        event = EventUpdate(name=event.name, deadline=event.deadline, status=EventStatus.closed)

        updated_event = await self.repo.update(event_id=event_id, event=event)

        return EventRead.from_orm(updated_event)

    async def finish(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status != EventStatus.closed:
            raise exceptions.UnexpectedEventStatus

        for match in event.matches:
            if match.status != MatchStatus.completed:
                raise exceptions.MatchesAreNotFinished

        data = EventUpdate(name=event.name, deadline=event.deadline, status=EventStatus.completed)

        updated_event = await self.repo.update(event_id=event_id, event=data)

        return EventRead.from_orm(updated_event)

    async def delete(self, event_id: int) -> None:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        return await self.repo.delete(event_id=event_id)
