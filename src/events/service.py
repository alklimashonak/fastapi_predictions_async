from typing import Sequence

from src import exceptions
from src.core.config import settings
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

    async def upgrade_status(self, event_id: int) -> EventRead:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status == EventStatus.completed:
            raise exceptions.UnexpectedEventStatus

        if event.status == EventStatus.closed:
            for match in event.matches:
                if match.status != MatchStatus.completed:
                    raise exceptions.MatchesAreNotFinished

        if event.status == EventStatus.created:
            if len(event.matches) != settings.MATCHES_COUNT:
                raise exceptions.TooFewMatches

        data = EventUpdate(name=event.name, deadline=event.deadline, status=event.status+1)

        updated_event = await self.repo.update(event_id=event_id, event=data)

        return EventRead.from_orm(updated_event)

    async def delete(self, event_id: int) -> None:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        return await self.repo.delete(event_id=event_id)
