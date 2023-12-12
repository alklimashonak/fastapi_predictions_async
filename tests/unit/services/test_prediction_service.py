import pytest

from src import exceptions
from src.matches.base import BaseMatchRepository
from src.matches.models import MatchStatus
from src.predictions.base import BasePredictionRepository, BasePredictionService
from src.predictions.schemas import PredictionRead, PredictionCreate, PredictionUpdate
from src.predictions.service import PredictionService
from tests.utils import PredictionModel, UserModel, MatchModel, EventModel


@pytest.fixture
def prediction_service(
        mock_prediction_repo: BasePredictionRepository,
        mock_match_repo: BaseMatchRepository,
) -> BasePredictionService:
    yield PredictionService(repo=mock_prediction_repo, match_repo=mock_match_repo)


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_not_existing_prediction(
            self,
            prediction_service: BasePredictionService,
    ) -> None:
        with pytest.raises(exceptions.PredictionNotFound):
            await prediction_service.get_by_id(prediction_id=987)

    async def test_get_existing_prediction(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
    ) -> None:
        prediction = await prediction_service.get_by_id(prediction_id=prediction1.id)

        assert type(prediction) == PredictionRead
        assert prediction.id == prediction1.id
        assert prediction.home_goals == prediction1.home_goals
        assert prediction.away_goals == prediction1.away_goals


@pytest.mark.asyncio
class TestGetMultipleByEventID:
    async def test_get_predictions_works(
            self,
            prediction_service: BasePredictionService,
            active_user: UserModel,
            prediction1: PredictionModel,
            upcoming_event: EventModel,
    ) -> None:
        predictions = await prediction_service.get_multiple_by_event_id(
            event_id=upcoming_event.id,
            user_id=active_user.id
        )

        assert len(predictions) > 0
        assert type(predictions[0]) == PredictionRead


@pytest.mark.asyncio
class TestCreatePrediction:
    async def test_match_is_not_existing(
            self,
            prediction_service: BasePredictionService,
            active_user: UserModel,
    ) -> None:
        prediction_data = PredictionCreate(
            home_goals=1,
            away_goals=1,
            match_id=987,
        )

        with pytest.raises(exceptions.MatchNotFound):
            await prediction_service.create(prediction=prediction_data, user_id=active_user.id)

    async def test_prediction_already_exists(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
    ) -> None:
        prediction_data = PredictionCreate(
            home_goals=1,
            away_goals=1,
            match_id=prediction1.match_id,
        )

        with pytest.raises(exceptions.PredictionAlreadyExists):
            await prediction_service.create(prediction=prediction_data, user_id=prediction1.user_id)

    async def test_created_prediction_has_not_points(
            self,
            prediction_service: BasePredictionService,
            superuser: UserModel,
            upcoming_match: MatchModel,
    ) -> None:
        prediction_data = PredictionCreate(
            home_goals=2,
            away_goals=1,
            match_id=upcoming_match.id,
        )

        prediction = await prediction_service.create(prediction=prediction_data, user_id=superuser.id)

        assert type(prediction) == PredictionRead
        assert prediction.home_goals == prediction_data.home_goals
        assert prediction.away_goals == prediction_data.away_goals
        assert prediction.points is None

    async def test_create_prediction_for_ongoing_match(
            self,
            prediction_service: BasePredictionService,
            superuser: UserModel,
            ongoing_match: MatchModel,
    ) -> None:
        prediction_data = PredictionCreate(
            home_goals=2,
            away_goals=1,
            match_id=ongoing_match.id,
        )

        with pytest.raises(exceptions.UnexpectedMatchStatus):
            await prediction_service.create(prediction=prediction_data, user_id=superuser.id)

    async def test_create_prediction_for_completed_match(
            self,
            prediction_service: BasePredictionService,
            superuser: UserModel,
            completed_match: MatchModel,
    ) -> None:
        prediction_data = PredictionCreate(
            home_goals=2,
            away_goals=1,
            match_id=completed_match.id,
        )

        with pytest.raises(exceptions.UnexpectedMatchStatus):
            await prediction_service.create(prediction=prediction_data, user_id=superuser.id)


@pytest.mark.asyncio
class TestUpdatePrediction:
    async def test_update_not_existing_prediction(
            self,
            prediction_service: BasePredictionService,
            active_user: UserModel,
    ) -> None:
        prediction_data = PredictionUpdate(
            home_goals=2,
            away_goals=0,
        )

        with pytest.raises(exceptions.PredictionNotFound):
            await prediction_service.update(prediction_id=987, prediction=prediction_data, user_id=active_user.id)

    async def test_update_not_own_prediction(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            active_user: UserModel,
            superuser: UserModel,
    ) -> None:
        prediction_data = PredictionUpdate(
            home_goals=3,
            away_goals=0,
        )

        assert prediction1.user_id == active_user.id

        with pytest.raises(exceptions.UserIsNotAllowed):
            await prediction_service.update(
                prediction_id=prediction1.id, prediction=prediction_data, user_id=superuser.id
            )

    async def test_update_prediction_for_ongoing_match(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            active_user: UserModel,
            upcoming_match: MatchModel,
    ) -> None:
        upcoming_match.status = MatchStatus.ongoing

        prediction_data = PredictionUpdate(
            home_goals=5,
            away_goals=0,
        )

        with pytest.raises(exceptions.UnexpectedMatchStatus):
            await prediction_service.update(
                prediction=prediction_data, prediction_id=prediction1.id, user_id=active_user.id
            )

    async def test_update_prediction_for_completed_match(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            active_user: UserModel,
            upcoming_match: MatchModel,
    ) -> None:
        upcoming_match.status = MatchStatus.completed

        prediction_data = PredictionUpdate(
            home_goals=5,
            away_goals=0,
        )

        with pytest.raises(exceptions.UnexpectedMatchStatus):
            await prediction_service.update(
                prediction=prediction_data, prediction_id=prediction1.id, user_id=active_user.id
            )

    async def test_update_prediction_successfully(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            active_user: UserModel,
    ) -> None:
        prediction_data = PredictionUpdate(
            home_goals=5,
            away_goals=0,
        )

        prediction = await prediction_service.update(
            prediction=prediction_data, prediction_id=prediction1.id, user_id=active_user.id
        )

        assert type(prediction) == PredictionRead
        assert prediction.id == prediction1.id
        assert prediction.home_goals == prediction_data.home_goals
        assert prediction.away_goals == prediction_data.away_goals
        assert prediction.match_id == prediction1.match_id
