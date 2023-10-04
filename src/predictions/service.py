import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from src.matches.base import BaseMatchRepository
from src.predictions.base import BasePredictionService, BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate, PredictionRead

logger = logging.getLogger(__name__)


class PredictionService(BasePredictionService):
    def __init__(self, repo: BasePredictionRepository, match_repo: BaseMatchRepository):
        self.repo = repo
        self.match_repo = match_repo

    async def get_by_id(self, prediction_id: int) -> PredictionRead:
        prediction = await self.repo.get_by_id(prediction_id=prediction_id)

        if not prediction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Prediction not found')
        return PredictionRead.from_orm(prediction)

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> Sequence[PredictionRead]:
        predictions = await self.repo.get_multiple_by_event_id(event_id=event_id, user_id=user_id)

        return [PredictionRead.from_orm(prediction) for prediction in predictions]

    async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionRead:
        if not await self.match_repo.get_by_id(match_id=prediction.match_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Match does not exists'
            )

        if await self.repo.exists_in_db(user_id=user_id, match_id=prediction.match_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Prediction for this match already exists',
            )

        prediction = await self.repo.create(prediction=prediction, user_id=user_id)
        return PredictionRead.from_orm(prediction)

    async def update(self, prediction_id: int, prediction: PredictionUpdate, user_id: UUID) -> PredictionRead:
        predict = await self.repo.get_by_id(prediction_id=prediction_id)

        if not predict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Prediction not found')

        if predict.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You can only edit your own predictions')

        predict = await self.repo.update(prediction_id=prediction_id, prediction=prediction)

        return PredictionRead.from_orm(predict)
