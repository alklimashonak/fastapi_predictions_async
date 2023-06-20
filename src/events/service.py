from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.events.base import BaseEventDatabase
from src.events.models import Event, Match, EP
from src.events.schemas import EventCreate, MatchCreate, EventUpdate, MatchUpdate


class EventDatabase(BaseEventDatabase):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events(self):
        stmt = select(Event).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_event_by_id(self, event_id: int) -> EP | None:
        stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.matches))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_event(self, event: EventCreate) -> EP | None:
        stmt = insert(Event).values(**event.dict(exclude={'matches'})).returning(Event.id)
        result = await self.session.execute(stmt)
        event_id = result.scalar_one_or_none()

        for match in event.matches:
            await self._create_match(match=match, event_id=event_id)

        await self.session.commit()
        return await self.get_event_by_id(event_id=event_id)

    async def update_event(self, event: EventUpdate, event_id: int) -> EP | None:
        stmt = update(Event) \
            .where(Event.id == event_id) \
            .values(**event.dict(exclude={'new_matches', 'matches_to_update', 'matches_to_delete'}))
        await self.session.execute(stmt)

        for match in event.new_matches:
            await self._create_match(match=match, event_id=event_id)

        for match in event.matches_to_update:
            await self._update_match(match=match)

        for match_id in event.matches_to_delete:
            await self._delete_match(match_id=match_id)

        await self.session.commit()
        return await self.get_event_by_id(event_id=event_id)

    async def delete_event(self, event_id: int) -> None:
        stmt = delete(Event).where(Event.id == event_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def _create_match(self, match: MatchCreate, event_id: int) -> None:
        stmt = insert(Match).values(**match.dict(), event_id=event_id).returning(Match.id)
        await self.session.execute(stmt)

    async def _update_match(self, match: MatchUpdate) -> None:
        stmt = update(Match).where(Match.id == match.id).values(**match.dict()).returning(Match.id)
        await self.session.execute(stmt)

    async def _delete_match(self, match_id: int) -> None:
        stmt = delete(Match).where(Match.id == match_id)
        await self.session.execute(stmt)
