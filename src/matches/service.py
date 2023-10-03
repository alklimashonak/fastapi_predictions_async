from fastapi import HTTPException
from starlette import status

from src.events.models import Match
from src.events.schemas import MatchCreate
from src.matches.base import BaseMatchService, BaseMatchRepository


class MatchService(BaseMatchService):
    def __init__(self, repo: BaseMatchRepository):
        self.repo = repo

    async def create(self, match: MatchCreate, event_id: int) -> Match:
        return await self.repo.create(match=match, event_id=event_id)

    async def delete(self, match_id: int) -> None:
        event = await self.repo.get_by_id(match_id=match_id)

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')

        return await self.repo.delete(match_id=match_id)
