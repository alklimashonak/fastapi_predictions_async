from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.events.service import EventDatabase


async def get_event_db(session: AsyncSession = Depends(get_async_session)):
    yield EventDatabase(session)
