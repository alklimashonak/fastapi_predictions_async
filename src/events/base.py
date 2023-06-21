from src.events.models import Event
from src.events.schemas import EventCreate, EventUpdate


class BaseEventDatabase:
    async def get_events(self, offset: int, limit: int):
        raise NotImplementedError()

    async def get_event_by_id(self, event_id: int) -> Event | None:
        raise NotImplementedError()

    async def create_event(self, event: EventCreate) -> Event | None:
        raise NotImplementedError()

    async def update_event(self, event: EventUpdate, event_id: int) -> Event | None:
        raise NotImplementedError()

    async def delete_event(self, event_id: int) -> None:
        raise NotImplementedError()
