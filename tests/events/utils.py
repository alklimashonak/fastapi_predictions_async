import contextlib
from datetime import datetime

from src.events.dependencies import get_event_db
from src.events.models import EP
from src.events.schemas import MatchCreate, EventCreate
from tests.conftest import get_async_session_context


get_event_db_context = contextlib.asynccontextmanager(get_event_db)


async def create_event(
        name: str,
        matches: list[MatchCreate]
) -> EP | None:
    async with get_async_session_context() as session:
        async with get_event_db_context(session) as db:
            event = EventCreate(
                name=name,
                start_time=datetime.utcnow(),
                matches=matches
            )
            return await db.create_event(event=event)
