import logging
import uuid

import pytest
from fastapi import HTTPException

from src.auth.models import User
from src.events.models import Event
from src.predictions.models import Prediction
from src.predictions.base import BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestGetPredictions:
    async def test_get_prediction_by_id_returns_prediction(
            self, test_prediction: Prediction, prediction_repo: BasePredictionRepository
    ) -> None:
        prediction = await prediction_repo.get_by_id(prediction_id=test_prediction.id)

        assert prediction.id == test_prediction.id
        assert prediction.match_id == test_prediction.match_id

    async def test_get_predictions_by_event_id_returns_list(
            self,
            test_user: User,
            test_event: Event,
            test_prediction: Prediction,
            prediction_repo: BasePredictionRepository
    ) -> None:
        predictions = await prediction_repo.get_multiple_by_event_id(user_id=test_user.id, event_id=test_event.id)

        assert len(predictions) == 1
        assert predictions[0].id == test_prediction.id


@pytest.mark.asyncio
class TestCreatePrediction:
    async def test_create_prediction_works(
            self, test_event: Event, test_user: User, prediction_repo: BasePredictionRepository
    ) -> None:
        match_id = test_event.matches[0].id
        prediction_data = PredictionCreate(
                home_goals=1,
                away_goals=1,
                match_id=match_id,
            )

        prediction = await prediction_repo.create(prediction=prediction_data, user_id=test_user.id)

        assert prediction.id
        assert prediction.user_id == test_user.id
        assert prediction.match_id == prediction_data.match_id
        assert prediction.home_goals == prediction_data.home_goals
        assert prediction.away_goals == prediction_data.away_goals


@pytest.mark.asyncio
class TestPredictionUpdate:
    async def test_update_prediction_works(
            self,
            test_prediction: Prediction,
            prediction_repo: BasePredictionRepository
    ) -> None:
        updated_data = PredictionUpdate(
            home_goals=3,
            away_goals=3,
        )

        updated_prediction = await prediction_repo.update(prediction_id=test_prediction.id, prediction=updated_data)

        assert test_prediction.id == updated_prediction.id
        assert test_prediction.home_goals != updated_prediction.home_goals
        assert test_prediction.away_goals != updated_prediction.away_goals


@pytest.mark.asyncio
class TestExistsInDB:
    async def test_prediction_in_db_returns_true(
            self,
            prediction_repo: BasePredictionRepository,
            test_prediction: Prediction,
    ) -> None:
        exists_in_db = await prediction_repo.exists_in_db(
            user_id=test_prediction.user_id,
            match_id=test_prediction.match_id
        )

        assert exists_in_db is True

    async def test_prediction_doesnt_exists_returns_false(
            self,
            prediction_repo: BasePredictionRepository,
    ) -> None:
        exists_in_db = await prediction_repo.exists_in_db(
            user_id=uuid.uuid4(),
            match_id=99999
        )

        assert exists_in_db is False
