from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.events.base import BaseEventRepository
from src.events.dependencies import get_event_repo
from src.predictions.base import BasePredictionRepository
from src.predictions.repo import PredictionRepository
from src.predictions.service import PredictionService


async def get_prediction_repo(session: AsyncSession = Depends(get_async_session)):
    yield PredictionRepository(session)


async def get_prediction_service(
        repo: BasePredictionRepository = Depends(get_prediction_repo),
        event_repo: BaseEventRepository = Depends(get_event_repo),
):
    yield PredictionService(repo, event_repo=event_repo)
