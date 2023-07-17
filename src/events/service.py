from fastapi import Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_async_session
from src.events.base import BaseEventService
from src.events.models import Event, Match
from src.events.schemas import EventCreate, MatchCreate


class EventService(BaseEventService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_multiple(self, offset: int = 0, limit: int = 100):
        stmt = select(Event).options(selectinload(Event.matches)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, event_id: int) -> Event | None:
        stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, event: EventCreate) -> Event:
        new_event = Event(**event.dict(exclude={'matches'}))
        self.session.add(new_event)
        await self.session.flush([new_event])

        await self._create_matches(matches=event.matches, event_id=new_event.id)

        await self.session.commit()
        return await self.get_by_id(event_id=new_event.id)

    async def delete(self, event_id: int) -> None:
        stmt = delete(Event).where(Event.id == event_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def _create_matches(self, matches: list[MatchCreate], event_id: int) -> None:
        match_models = [Match(**match.dict(), event_id=event_id) for match in matches]
        self.session.add_all(match_models)


async def get_event_service(session: AsyncSession = Depends(get_async_session)):
    yield EventService(session)
