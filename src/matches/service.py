from fastapi import HTTPException
from starlette import status

from src.events.base import BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import MatchCreate
from src.matches.base import BaseMatchService, BaseMatchRepository
from src.matches.schemas import MatchRead


class MatchService(BaseMatchService):
    def __init__(self, repo: BaseMatchRepository, event_repo: BaseEventRepository):
        self.repo = repo
        self.event_repo = event_repo

    async def create(self, match: MatchCreate, event_id: int) -> MatchRead:
        event = await self.event_repo.get_by_id(event_id=event_id)

        if event.status != EventStatus.created:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Only events with status "Created" can add a match'
            )

        new_match = await self.repo.create(match=match, event_id=event_id)

        return MatchRead.from_orm(new_match)

    async def delete(self, match_id: int) -> None:
        event = await self.repo.get_by_id(match_id=match_id)

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')

        return await self.repo.delete(match_id=match_id)
