from typing import Sequence

from fastapi import HTTPException
from starlette import status

from src.events.base import BaseEventService, BaseEventRepository
from src.events.models import Event
from src.events.schemas import EventCreate


class EventService(BaseEventService):
    def __init__(self, repo: BaseEventRepository):
        self.repo = repo

    async def get_multiple(self, admin_mode: bool = False, offset: int = 0, limit: int = 100) -> Sequence[Event]:
        return await self.repo.get_multiple(admin_mode=admin_mode, offset=offset, limit=limit)

    async def get_by_id(self, event_id: int) -> Event:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
        return event

    async def create(self, event: EventCreate) -> Event:
        return await self.repo.create(event=event)

    async def run(self, event_id: int) -> Event:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')

        if event.status != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can run only not started events')

        if len(event.matches) != 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Required min 5 matches')

        return await self.repo.run(event_id=event_id)

    async def delete(self, event_id: int) -> None:
        event = await self.repo.get_by_id(event_id=event_id)

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')

        return await self.repo.delete(event_id=event_id)
