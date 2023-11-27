from src import exceptions
from src.events.base import BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import MatchCreate
from src.matches.base import BaseMatchService, BaseMatchRepository
from src.matches.models import MatchStatus
from src.matches.schemas import MatchRead, MatchUpdate
from src.predictions.base import BasePredictionRepository


class MatchService(BaseMatchService):
    def __init__(
            self,
            repo: BaseMatchRepository,
            event_repo: BaseEventRepository,
            prediction_repo: BasePredictionRepository,
    ):
        self.repo = repo
        self.event_repo = event_repo
        self.prediction_repo = prediction_repo

    async def create(self, match: MatchCreate, event_id: int) -> MatchRead:
        event = await self.event_repo.get_by_id(event_id=event_id)

        if not event:
            raise exceptions.EventNotFound

        if event.status > EventStatus.created:
            raise exceptions.EventAlreadyIsRunning

        new_match = await self.repo.create(match=match, event_id=event_id)

        new_match = MatchRead.from_orm(new_match)

        return new_match

    async def finish(self, match_id, home_goals: int, away_goals: int) -> MatchRead:
        match = await self.repo.get_by_id(match_id=match_id)

        if not match:
            raise exceptions.MatchNotFound

        if match.status == MatchStatus.completed:
            raise exceptions.MatchAlreadyIsCompleted

        new_data = MatchUpdate(
            home_team=match.home_team,
            away_team=match.away_team,
            start_time=match.start_time,
            home_goals=home_goals,
            away_goals=away_goals,
            status=MatchStatus.completed,
        )

        updated_match = await self.repo.update(match_id=match_id, match=new_data)

        await self.prediction_repo.update_points_for_match(match=updated_match)

        return MatchRead.from_orm(updated_match)

    async def delete(self, match_id: int) -> None:
        match = await self.repo.get_by_id(match_id=match_id)

        if not match:
            raise exceptions.MatchNotFound

        return await self.repo.delete(match_id=match_id)
