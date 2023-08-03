from fastapi import APIRouter, Depends
from starlette import status

from src.auth.dependencies import get_current_superuser
from src.events.base import BaseEventService
from src.events.dependencies import get_event_service
from src.events.schemas import EventRead, EventCreate

router = APIRouter()


@router.get('', response_model=list[EventRead], response_model_exclude={'matches'})
async def get_events(
        event_service: BaseEventService = Depends(get_event_service),
        offset: int = 0,
        limit: int = 100,
):
    return await event_service.get_multiple(offset=offset, limit=limit)


@router.get('/{event_id}', response_model=EventRead)
async def get_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service)
):
    return await event_service.get_by_id(event_id=event_id)


@router.post(
    '',
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_superuser)],
)
async def create_event(
        event: EventCreate,
        event_service: BaseEventService = Depends(get_event_service)
):
    return await event_service.create(event=event)


@router.delete('/{event_id}', dependencies=[Depends(get_current_superuser)])
async def delete_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service)
):
    return await event_service.delete(event_id=event_id)
