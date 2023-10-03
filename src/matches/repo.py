from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import Match
from src.events.schemas import MatchCreate
from src.matches.base import BaseMatchRepository


class MatchRepository(BaseMatchRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, match_id: int) -> Match | None:
        stmt = select(Match).where(Match.id == match_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, match: MatchCreate, event_id: int) -> Match:
        new_match = Match(**match.dict(), event_id=event_id)

        self.session.add(new_match)
        await self.session.commit()
        await self.session.refresh(new_match)
        return new_match

    async def delete(self, match_id: int) -> None:
        stmt = delete(Match).where(Match.id == match_id)
        await self.session.execute(stmt)
        await self.session.commit()
