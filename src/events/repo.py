from typing import Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.events.base import BaseEventRepository
from src.events.models import Event, EventStatus
from src.events.schemas import EventCreate


class EventRepository(BaseEventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_multiple(self, admin_mode: bool = False, offset: int = 0, limit: int = 100) -> Sequence[Event]:
        if admin_mode:
            stmt = select(Event) \
                .options(selectinload(Event.matches)) \
                .order_by(Event.deadline) \
                .offset(offset) \
                .limit(limit)
        else:
            stmt = select(Event) \
                .options(selectinload(Event.matches)) \
                .filter(Event.status != EventStatus.created) \
                .order_by(Event.deadline) \
                .offset(offset) \
                .limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, event_id: int) -> Event | None:
        stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, event: EventCreate) -> Event:
        new_event = Event(**event.dict())

        self.session.add(new_event)

        await self.session.commit()
        await self.session.refresh(new_event)

        return new_event

    async def run(self, event_id: int) -> Event:
        stmt = update(Event).where(Event.id == event_id).values(status=EventStatus.upcoming).returning(Event)
        result = await self.session.execute(stmt)

        await self.session.commit()

        return result.scalar_one_or_none()

    async def delete(self, event_id: int) -> None:
        stmt = delete(Event).where(Event.id == event_id)
        await self.session.execute(stmt)
        await self.session.commit()
