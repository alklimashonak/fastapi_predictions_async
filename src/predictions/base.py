from typing import Sequence
from uuid import UUID

from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate, PredictionRead


class BasePredictionRepository:
    async def get_by_id(self, prediction_id: int) -> Prediction | None:
        raise NotImplementedError

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> Sequence[Prediction]:
        raise NotImplementedError

    async def create(self, prediction: PredictionCreate, user_id: UUID) -> Prediction:
        raise NotImplementedError

    async def update(self, prediction_id: int, prediction: PredictionUpdate) -> Prediction | None:
        raise NotImplementedError

    async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
        raise NotImplementedError


class BasePredictionService:
    async def get_by_id(self, prediction_id: int) -> PredictionRead:
        raise NotImplementedError

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> Sequence[PredictionRead]:
        raise NotImplementedError

    async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionRead:
        raise NotImplementedError

    async def update(self, prediction_id: int, prediction: PredictionUpdate, user_id: UUID) -> PredictionRead:
        raise NotImplementedError
