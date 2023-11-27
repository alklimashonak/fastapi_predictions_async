from datetime import datetime

import pytest
from fastapi import HTTPException

from src import exceptions
from src.events.base import BaseEventRepository
from src.matches.base import BaseMatchService, BaseMatchRepository
from src.matches.models import MatchStatus
from src.matches.schemas import MatchCreate, MatchRead
from src.matches.service import MatchService
from src.predictions.base import BasePredictionRepository
from tests.utils import EventModel, MatchModel


@pytest.fixture
def match_service(
        mock_match_repo: BaseMatchRepository,
        mock_event_repo: BaseEventRepository,
        mock_prediction_repo: BasePredictionRepository,
) -> BaseMatchService:
    yield MatchService(repo=mock_match_repo, event_repo=mock_event_repo, prediction_repo=mock_prediction_repo)


@pytest.mark.asyncio
class TestCreate:
    async def test_event_does_not_exist(
            self,
            match_service: BaseMatchService,
    ) -> None:
        match_data = MatchCreate(
            home_team='Home team',
            away_team='Away team',
            start_time=datetime.utcnow(),
        )

        with pytest.raises(exceptions.EventNotFound):
            await match_service.create(match=match_data, event_id=987)

    async def test_event_has_not_created_status(
            self,
            match_service: BaseMatchService,
            upcoming_event: EventModel,
            ongoing_event: EventModel,
    ) -> None:
        match_data = MatchCreate(
            home_team='Home team',
            away_team='Away team',
            start_time=datetime.utcnow(),
        )

        with pytest.raises(exceptions.EventIsNotCreated):
            await match_service.create(match=match_data, event_id=upcoming_event.id)

        with pytest.raises(exceptions.EventIsNotCreated):
            await match_service.create(match=match_data, event_id=ongoing_event.id)

    async def test_match_successfully_created(
            self,
            match_service: BaseMatchService,
            created_event: EventModel,
    ) -> None:
        match_data = MatchCreate(
            home_team='Home team',
            away_team='Away team',
            start_time=datetime.utcnow(),
        )

        match = await match_service.create(match=match_data, event_id=created_event.id)

        assert type(match) == MatchRead
        assert match.home_team == match_data.home_team
        assert match.away_team == match_data.away_team
        assert match.start_time == match_data.start_time
        assert match.event_id == created_event.id
        assert match.status == MatchStatus.upcoming
        assert match.home_goals is None
        assert match.away_goals is None


@pytest.mark.asyncio
class TestFinishMatch:
    async def test_match_not_existing(
            self,
            match_service: BaseMatchService,
    ) -> None:
        with pytest.raises(exceptions.MatchNotFound):
            await match_service.finish(match_id=987, home_goals=1, away_goals=1)

    async def test_match_already_completed(
            self,
            match_service: BaseMatchService,
            completed_match: MatchModel,
    ) -> None:
        with pytest.raises(exceptions.MatchAlreadyIsCompleted):
            await match_service.finish(match_id=completed_match.id, home_goals=1, away_goals=1)

    async def test_ongoing_match_is_able_to_finish(
            self,
            match_service: BaseMatchService,
            ongoing_match: MatchModel,
    ) -> None:
        match = await match_service.finish(match_id=ongoing_match.id, home_goals=2, away_goals=2)

        assert type(match) == MatchRead
        assert match.status == MatchStatus.completed
        assert match.home_goals == 2
        assert match.away_goals == 2


@pytest.mark.asyncio
class TestDeleteMatch:
    async def test_delete_not_existing_match(
            self,
            match_service: BaseMatchService,
    ) -> None:
        with pytest.raises(exceptions.MatchNotFound):
            await match_service.delete(match_id=987)
