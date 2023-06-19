from src.events.models import EP
from src.events.schemas import EventCreate, EventUpdate


class BaseEventDatabase:
    async def get_events(self):
        raise NotImplementedError()

    async def get_event_by_id(self, event_id: int) -> EP | None:
        raise NotImplementedError()

    async def create_event(self, event: EventCreate) -> EP | None:
        raise NotImplementedError()

    async def update_event(self, event: EventUpdate, event_id: int) -> EP | None:
        raise NotImplementedError()

    async def delete_event(self, event_id: int) -> None:
        raise NotImplementedError()
