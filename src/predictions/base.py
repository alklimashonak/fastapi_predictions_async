from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


class BasePredictionService:
    async def get_multiple_by_event_id(self, event_id: int) -> list[Prediction]:
        raise NotImplementedError

    async def create(self, prediction: PredictionCreate) -> Prediction:
        raise NotImplementedError

    async def update(self, prediction: PredictionUpdate) -> Prediction:
        raise NotImplementedError
