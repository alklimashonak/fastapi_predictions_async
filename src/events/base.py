from typing import Sequence

from src.events.models import Event
from src.events.schemas import EventCreate


class BaseEventRepository:
    async def get_multiple(self, admin_mode: bool, offset: int = 0, limit: int = 100) -> Sequence[Event]:
        raise NotImplementedError

    async def get_by_id(self, event_id: int) -> Event | None:
        raise NotImplementedError

    async def create(self, event: EventCreate) -> Event:
        raise NotImplementedError

    async def run(self, event_id: int) -> Event:
        raise NotImplementedError

    async def delete(self, event_id: int) -> None:
        raise NotImplementedError


class BaseEventService:
    async def get_multiple(self, admin_mode: bool, offset: int = 0, limit: int = 100) -> Sequence[Event]:
        raise NotImplementedError

    async def get_by_id(self, event_id: int) -> Event | None:
        raise NotImplementedError

    async def create(self, event: EventCreate) -> Event:
        raise NotImplementedError

    async def run(self, event_id: int) -> Event:
        raise NotImplementedError

    async def delete(self, event_id: int) -> None:
        raise NotImplementedError
