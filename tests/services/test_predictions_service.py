import logging
from typing import Callable

import pytest
from fastapi import HTTPException

from src.core.security import get_password_hash
from src.predictions.base import BasePredictionService
from src.predictions.schemas import PredictionCreate, PredictionUpdate
from src.predictions.service import PredictionService
from tests.utils import UserModel, EventModel, MatchModel, PredictionModel

logger = logging.getLogger(__name__)


@pytest.fixture
def prediction_service(
        mock_prediction_repo: Callable,
        mock_match_repo: Callable,
        superuser: UserModel,
        active_user: UserModel,
        event1: EventModel,
        match1: MatchModel,
        prediction1: PredictionModel,
        prediction2: PredictionModel,
) -> BasePredictionService:
    prediction_repo = mock_prediction_repo(
        users=[superuser, active_user],
        events=[event1],
        predictions=[prediction1, prediction2]
    )
    match_repo = mock_match_repo(matches=[match1])
    yield PredictionService(prediction_repo, match_repo)


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_existent_prediction_returns_prediction(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
    ) -> None:
        prediction = await prediction_service.get_by_id(prediction_id=prediction1.id)

        assert prediction.id == prediction1.id
        assert prediction.match_id == prediction1.match_id
        assert prediction.user_id == prediction1.user_id
        assert prediction.home_goals == prediction1.home_goals
        assert prediction.away_goals == prediction1.away_goals

    async def test_get_not_existent_prediction_raises_http_exc(
            self,
            prediction_service: BasePredictionService,
    ) -> None:
        with pytest.raises(HTTPException):
            await prediction_service.get_by_id(prediction_id=9339)


@pytest.mark.asyncio
class TestGetMultipleByEventID:
    async def test_get_multiple_by_event_id_works(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            prediction2: PredictionModel,
            event1: EventModel,
            active_user: UserModel,
            superuser: UserModel,
    ) -> None:
        predictions1 = await prediction_service.get_multiple_by_event_id(event_id=event1.id, user_id=active_user.id)
        predictions2 = await prediction_service.get_multiple_by_event_id(event_id=event1.id, user_id=superuser.id)

        assert len(predictions1) == 1
        assert len(predictions2) == 1
        assert predictions1[0].id != predictions2[0].id


@pytest.mark.asyncio
class TestCreate:
    async def test_create_works_correctly(
            self,
            prediction_service: BasePredictionService,
            match1: MatchModel,
    ) -> None:
        user = UserModel(
            email='newuser@domen.com',
            hashed_password=get_password_hash('1234'),
        )

        prediction = PredictionCreate(
            home_goals=1,
            away_goals=0,
            match_id=match1.id,
        )

        new_prediction = await prediction_service.create(prediction=prediction, user_id=user.id)

        assert new_prediction
        assert hasattr(new_prediction, 'id')
        assert new_prediction.user_id == user.id
        assert new_prediction.match_id == match1.id
        assert new_prediction.home_goals == prediction.home_goals
        assert new_prediction.away_goals == prediction.away_goals

    async def test_create_for_non_existent_match_returns_http_exc(
            self,
            prediction_service: BasePredictionService,
            active_user: UserModel,
    ) -> None:
        new_prediction = PredictionCreate(
            home_goals=1,
            away_goals=0,
            match_id=9999,
        )
        with pytest.raises(HTTPException):
            await prediction_service.create(prediction=new_prediction, user_id=active_user.id)

    async def test_create_already_exists_raises_http_exc(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
    ) -> None:
        new_prediction = PredictionCreate(
            home_goals=2,
            away_goals=0,
            match_id=prediction1.match_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await prediction_service.create(prediction=new_prediction, user_id=prediction1.user_id)
        logger.warning(f'exc: {exc_info.value.detail}')


@pytest.mark.asyncio
class TestUpdate:
    async def test_user_can_update_his_prediction(
            self,
            prediction_service: BasePredictionService,
            prediction1: PredictionModel,
            active_user: UserModel,
    ) -> None:
        data = PredictionUpdate(
            home_goals=4,
            away_goals=0,
        )

        updated_prediction = await prediction_service.update(
            prediction_id=prediction1.id,
            prediction=data,
            user_id=active_user.id
        )

        assert updated_prediction.id == prediction1.id

    async def test_prediction_does_not_exist_raises_http_exc(
            self,
            prediction_service: BasePredictionService,
            active_user: UserModel,
    ) -> None:
        data = PredictionUpdate(
            home_goals=2,
            away_goals=2,
        )

        with pytest.raises(HTTPException):
            await prediction_service.update(prediction_id=2131, prediction=data, user_id=active_user.id)

    async def test_user_can_not_update_if_does_not_own(
            self,
            prediction_service: BasePredictionService,
            prediction2: PredictionModel,
            active_user: UserModel,
    ) -> None:
        data = PredictionUpdate(
            home_goals=5,
            away_goals=4,
        )

        with pytest.raises(HTTPException):
            await prediction_service.update(prediction_id=prediction2.id, prediction=data, user_id=active_user.id)

        assert prediction2.user_id != active_user.id
