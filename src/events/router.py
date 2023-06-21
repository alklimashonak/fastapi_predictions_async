from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.authentication import Authenticator
from starlette import status

from src.auth.config import get_superuser
from src.events.dependencies import get_event_db
from src.events.schemas import EventSchema, EventCreate, EventUpdate
from src.events.service import EventDatabase


def get_events_router(authenticator: Authenticator | None = None):
    """
    :param authenticator: required for tests
    :return:
    """
    router = APIRouter(prefix='/events', tags=['Events'])

    if authenticator:
        get_current_superuser = authenticator.current_user(
            active=True, verified=False, superuser=True
        )
    else:
        get_current_superuser = get_superuser

    @router.get('', response_model=list[EventSchema])
    async def get_events(
            event_db: EventDatabase = Depends(get_event_db),
            offset: int = 0,
            limit: int = 100,
    ):
        return await event_db.get_events(offset=offset, limit=limit)

    @router.get('/{event_id}', response_model=EventSchema)
    async def get_event(
            event_id: int,
            event_db: EventDatabase = Depends(get_event_db)
    ):
        event = await event_db.get_event_by_id(event_id=event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='event not found')
        return event

    @router.post(
        '',
        response_model=EventSchema,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(get_current_superuser)]
    )
    async def create_event(
            event: EventCreate,
            event_db: EventDatabase = Depends(get_event_db)
    ):
        return await event_db.create_event(event=event)

    @router.put('/{event_id}', response_model=EventSchema, dependencies=[Depends(get_current_superuser)])
    async def update_event(
            event: EventUpdate,
            event_id: int,
            event_db: EventDatabase = Depends(get_event_db)
    ):
        if not await event_db.get_event_by_id(event_id=event_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='event not found')
        return await event_db.update_event(event=event, event_id=event_id)

    @router.delete('/{event_id}', dependencies=[Depends(get_current_superuser)])
    async def delete_event(
            event_id: int,
            event_db: EventDatabase = Depends(get_event_db)
    ):
        if not await event_db.get_event_by_id(event_id=event_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='event not found')
        return await event_db.delete_event(event_id=event_id)

    return router
