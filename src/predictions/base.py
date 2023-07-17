from typing import Sequence

from pydantic import UUID4

from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


class BasePredictionService:
    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID4) -> Sequence[Prediction]:
        raise NotImplementedError

    async def get_by_id(self, prediction_id: int) -> Prediction:
        raise NotImplementedError

    async def create(self, prediction: PredictionCreate, user_id: UUID4) -> Prediction:
        raise NotImplementedError

    async def update(self, prediction_id: int, prediction: PredictionUpdate) -> Prediction:
        raise NotImplementedError

    async def create_one(self, prediction: PredictionCreate, user_id: UUID4) -> Prediction:
        raise NotImplementedError
