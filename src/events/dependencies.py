from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.events.repo import EventRepository
from src.events.service import EventService


async def get_event_repo(session: AsyncSession = Depends(get_async_session)):
    yield EventRepository(session)


async def get_event_service(repo: EventRepository = Depends(get_event_repo)):
    yield EventService(repo)
