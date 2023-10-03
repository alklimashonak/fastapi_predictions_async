from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.events.models import Match
from src.predictions.base import BasePredictionRepository
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


class PredictionRepository(BasePredictionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, prediction_id: int) -> Prediction | None:
        stmt = select(Prediction).where(Prediction.id == prediction_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> Sequence[Prediction]:
        stmt = select(Prediction) \
            .join(Prediction.match) \
            .options(joinedload(Prediction.match)) \
            .filter(Prediction.user_id == user_id) \
            .filter(Match.event_id == event_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, prediction: PredictionCreate, user_id: UUID) -> Prediction:
        new_prediction = Prediction(**prediction.dict(), user_id=user_id)

        self.session.add(new_prediction)

        await self.session.commit()
        await self.session.refresh(new_prediction)

        return new_prediction

    async def update(self, prediction_id: int, prediction: PredictionUpdate) -> Prediction | None:
        stmt = update(Prediction).values(**prediction.dict()).where(Prediction.id == prediction_id).returning(Prediction)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.scalar_one_or_none()

    async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
        stmt = select(Prediction).where(Prediction.user_id == user_id, Prediction.match_id == match_id)

        result = await self.session.execute(stmt)

        if result.scalar_one_or_none():
            return True
        return False
