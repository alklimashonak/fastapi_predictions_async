from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.auth.config import get_superuser
from src.events.dependencies import get_event_db
from src.events.schemas import EventSchema, EventCreate, EventUpdate
from src.events.service import EventDatabase

router = APIRouter()


@router.get('', response_model=list[EventSchema])
async def get_events(
        event_db: EventDatabase = Depends(get_event_db)
):
    return await event_db.get_events()


@router.get('/{event_id}', response_model=EventSchema)
async def get_event(
        event_id: int,
        event_db: EventDatabase = Depends(get_event_db)
):
    event = await event_db.get_event_by_id(event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='event not found')
    return event


@router.post('', response_model=EventSchema, dependencies=[Depends(get_superuser)])
async def create_event(
        event: EventCreate,
        event_db: EventDatabase = Depends(get_event_db)
):
    return await event_db.create_event(event=event)


@router.put('/{event_id}', response_model=EventSchema, dependencies=[Depends(get_superuser)])
async def update_event(
        updated_event: EventUpdate,
        event_id: int,
        event_db: EventDatabase = Depends(get_event_db)
):
    return await event_db.update_event(updated_event=updated_event, event_id=event_id)


@router.delete('/{event_id}', response_model=EventSchema, dependencies=[Depends(get_superuser)])
async def delete_event(
        event_id: int,
        event_db: EventDatabase = Depends(get_event_db)
):
    return await event_db.delete_event(event_id=event_id)
