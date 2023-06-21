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
        new_event = Event(**event.dict(exclude={'matches'}))
        self.session.add(new_event)
        await self.session.flush([new_event])

        await self._create_matches(matches=event.matches, event_id=new_event.id)

        await self.session.commit()
        return await self.get_event_by_id(event_id=new_event.id)

    async def update_event(self, event: EventUpdate, event_id: int) -> EP | None:
        stmt = update(Event) \
            .where(Event.id == event_id) \
            .values(**event.dict(exclude={'new_matches', 'matches_to_update', 'matches_to_delete'}))
        await self.session.execute(stmt)

        await self._create_matches(matches=event.new_matches, event_id=event_id)
        await self._update_matches(matches=event.matches_to_update)
        await self._delete_matches(matches=event.matches_to_delete)

        await self.session.commit()
        return await self.get_event_by_id(event_id=event_id)

    async def delete_event(self, event_id: int) -> None:
        stmt = delete(Event).where(Event.id == event_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def _create_matches(self, matches: list[MatchCreate], event_id: int) -> None:
        match_models = [Match(**match.dict(), event_id=event_id) for match in matches]
        self.session.add_all(match_models)

    async def _update_matches(self, matches: list[MatchUpdate]) -> None:
        for match in matches:
            stmt = update(Match).where(Match.id == match.id).values(**match.dict())
            await self.session.execute(stmt)

    async def _delete_matches(self, matches: list[int]) -> None:
        stmt = delete(Match).where(Match.id.in_(matches))
        await self.session.execute(stmt)
