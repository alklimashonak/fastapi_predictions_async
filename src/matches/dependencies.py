from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.events.base import BaseEventRepository
from src.events.dependencies import get_event_repo
from src.matches.repo import MatchRepository
from src.matches.service import MatchService
from src.predictions.repo import PredictionRepository


async def get_match_repo(session: AsyncSession = Depends(get_async_session)):
    yield MatchRepository(session)


async def get_match_service(
        session: AsyncSession = Depends(get_async_session),
        repo: MatchRepository = Depends(get_match_repo),
        event_repo: BaseEventRepository = Depends(get_event_repo),
):
    prediction_repo = PredictionRepository(session=session)
    yield MatchService(repo, event_repo=event_repo, prediction_repo=prediction_repo)
