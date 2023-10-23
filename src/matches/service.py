from fastapi import HTTPException
from starlette import status

from src.events.base import BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import MatchCreate
from src.matches.base import BaseMatchService, BaseMatchRepository
from src.matches.models import MatchStatus
from src.matches.schemas import MatchRead, MatchUpdate


class MatchService(BaseMatchService):
    def __init__(self, repo: BaseMatchRepository, event_repo: BaseEventRepository):
        self.repo = repo
        self.event_repo = event_repo

    async def create(self, match: MatchCreate, event_id: int) -> MatchRead:
        event = await self.event_repo.get_by_id(event_id=event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Event not found'
            )

        if event.status != EventStatus.created:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Only events with status "Created" can add a match'
            )

        new_match = await self.repo.create(match=match, event_id=event_id)

        return MatchRead.from_orm(new_match)

    async def finish(self, match_id, home_goals: int, away_goals: int) -> MatchRead:
        match = await self.repo.get_by_id(match_id=match_id)

        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Match not found')

        if match.status > MatchStatus.upcoming:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Match is already finished')

        new_data = MatchUpdate(
            home_team=match.home_team,
            away_team=match.away_team,
            start_time=match.start_time,
            home_goals=home_goals,
            away_goals=away_goals,
            status=MatchStatus.completed,
        )

        return await self.repo.update(match_id=match_id, match=new_data)

    async def delete(self, match_id: int) -> None:
        match = await self.repo.get_by_id(match_id=match_id)

        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Match not found')

        return await self.repo.delete(match_id=match_id)
