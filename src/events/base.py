from src.events.models import Event
from src.events.schemas import EventCreate, MatchCreate


class BaseEventService:
    async def get_multiple(self, offset: int, limit: int):
        raise NotImplementedError()

    async def get_by_id(self, event_id: int) -> Event | None:
        raise NotImplementedError()

    async def create(self, event: EventCreate) -> Event | None:
        raise NotImplementedError()

    async def delete(self, event_id: int) -> None:
        raise NotImplementedError()

    async def _create_matches(self, matches: list[MatchCreate], event_id: int) -> None:
        raise NotImplementedError()
