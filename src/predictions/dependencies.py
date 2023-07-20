from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.predictions.repo import PredictionRepository
from src.predictions.service import PredictionService


async def get_prediction_repo(session: AsyncSession = Depends(get_async_session)):
    yield PredictionRepository(session)


async def get_prediction_service(repo = Depends(get_prediction_repo)):
    yield PredictionService(repo)
