from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.matches.repo import MatchRepository
from src.matches.service import MatchService


async def get_match_repo(session: AsyncSession = Depends(get_async_session)):
    yield MatchRepository(session)


async def get_match_service(repo: MatchRepository = Depends(get_match_repo)):
    yield MatchService(repo)
