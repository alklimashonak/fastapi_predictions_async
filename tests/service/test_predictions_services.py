import logging

import pytest
from sqlalchemy.exc import IntegrityError

from src.auth.models import User
from src.events.models import Event
from src.predictions.base import BasePredictionService
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestGetPredictions:
    async def test_get_prediction_by_id_returns_prediction(
            self, test_predictions: list[Prediction], prediction_service: BasePredictionService
    ) -> None:
        test_prediction, _ = test_predictions
        prediction = await prediction_service.get_by_id(prediction_id=test_prediction.id)

        assert prediction.id == test_prediction.id
        assert prediction.match_id == test_prediction.match_id

    async def test_get_predictions_by_event_id_returns_list(
            self,
            test_user: User,
            test_event: Event,
            test_predictions: list[Prediction],
            prediction_service: BasePredictionService
    ) -> None:
        predictions = await prediction_service.get_multiple_by_event_id(user_id=test_user.id, event_id=test_event.id)

        assert len(predictions) == len(test_predictions)


@pytest.mark.asyncio
class TestCreatePrediction:
    async def test_create_predictions_works(
            self, test_event: Event, test_user: User, prediction_service: BasePredictionService
    ) -> None:
        predictions_data = [
            PredictionCreate(
                home_goals=1,
                away_goals=1,
                match_id=test_event.matches[0].id,
            )
        ]

        predictions = await prediction_service.create_multiple(predictions=predictions_data, user_id=test_user.id)

        assert len(predictions) == len(predictions_data)

    async def test_prediction_already_exists_raise_error(
            self,
            test_predictions: list[Prediction],
            prediction_service: BasePredictionService
    ) -> None:
        test_prediction, _ = test_predictions

        predictions_data = [
            PredictionCreate(
                home_goals=2,
                away_goals=2,
                match_id=test_prediction.match_id,
            )
        ]
        try:
            await prediction_service.create_multiple(predictions=predictions_data, user_id=test_prediction.user_id)
            assert False
        except IntegrityError:
            assert True
