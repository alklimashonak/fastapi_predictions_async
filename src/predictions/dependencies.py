from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.matches.base import BaseMatchRepository
from src.matches.dependencies import get_match_repo
from src.predictions.base import BasePredictionRepository
from src.predictions.repo import PredictionRepository
from src.predictions.service import PredictionService


async def get_prediction_repo(session: AsyncSession = Depends(get_async_session)):
    yield PredictionRepository(session)


async def get_prediction_service(
        repo: BasePredictionRepository = Depends(get_prediction_repo),
        match_repo: BaseMatchRepository = Depends(get_match_repo),
):
    yield PredictionService(repo, match_repo=match_repo)
