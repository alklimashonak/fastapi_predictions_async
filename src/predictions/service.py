from typing import Sequence

from fastapi import Depends
from pydantic import UUID4
from sqlalchemy import select, insert, update, Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, join

from src.database import get_async_session
from src.events.models import Match
from src.predictions.base import BasePredictionService
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


class PredictionService(BasePredictionService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, prediction_id: int) -> Prediction | None:
        stmt = select(Prediction).where(Prediction.id == prediction_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID4) -> Sequence[Prediction]:
        stmt = select(Prediction) \
            .join(Prediction.match) \
            .options(joinedload(Prediction.match)) \
            .filter(Prediction.user_id == user_id) \
            .filter(Match.event_id == event_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, prediction: PredictionCreate, user_id: UUID4) -> Prediction:
        new_prediction = Prediction(**prediction.dict(), user_id=user_id)

        self.session.add(new_prediction)
        await self.session.flush([new_prediction])
        await self.session.commit()
        return await self.get_by_id(prediction_id=new_prediction.id)

    async def update(self, prediction_id: int, prediction: PredictionUpdate) -> Prediction:
        stmt = update(Prediction).values(**prediction.dict()).where(Prediction.id == prediction_id)

        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(prediction_id=prediction_id)


async def get_prediction_service(session: AsyncSession = Depends(get_async_session)):
    yield PredictionService(session)