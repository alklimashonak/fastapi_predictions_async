from sqlalchemy import select, insert, delete, update, Row, Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.events.models import Event, Match
from src.events.schemas import EventCreate, MatchCreate, EventUpdate


class EventDatabase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events(self):
        stmt = select(Event).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_event_by_id(self, event_id: int) -> Event:
        stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_event(self, event: EventCreate) -> Event:
        stmt = insert(Event).values(**event.dict(exclude={'matches'})).returning(Event.id)
        result = await self.session.execute(stmt)
        event_id = result.scalar_one_or_none()
        for match in event.matches:
            await self._create_match(match=match, event_id=event_id)
        await self.session.commit()
        return await self.get_event_by_id(event_id=event_id)

    async def update_event(self, updated_event: EventUpdate, event_id: int) -> Event:
        for match_id in updated_event.matches_to_delete:
            await self._delete_match(match_id=match_id)

        stmt = update(Event) \
            .where(Event.id == event_id) \
            .values(**updated_event.dict(exclude={'matches', 'matches_to_delete'})) \
            .returning(Event.id)
        await self.session.execute(stmt)

        for match in updated_event.matches:
            await self._create_match(match=match, event_id=event_id)

        await self.session.commit()
        return await self.get_event_by_id(event_id=event_id)

    async def delete_event(self, event_id: int) -> Event:
        event = await self.get_event_by_id(event_id=event_id)
        stmt = delete(Event).where(Event.id == event_id)
        await self.session.execute(stmt)
        return event

    async def _create_match(self, match: MatchCreate, event_id: int) -> None:
        stmt = insert(Match).values(**match.dict(), event_id=event_id)
        await self.session.execute(stmt)

    async def _delete_match(self, match_id: int) -> None:
        stmt = delete(Match).where(Match.id == match_id)
        await self.session.execute(stmt)
