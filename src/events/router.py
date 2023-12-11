from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src import exceptions
from src.auth.dependencies import get_current_superuser
from src.events.base import BaseEventService
from src.events.dependencies import get_event_service
from src.events.schemas import EventRead, EventCreate

router = APIRouter()


@router.get('', response_model=list[EventRead], response_model_exclude={'matches'})
async def get_events(
        event_service: BaseEventService = Depends(get_event_service),
        admin_mode: bool = False,
        offset: int = 0,
        limit: int = 100,
):
    return await event_service.get_multiple(admin_mode=admin_mode, offset=offset, limit=limit)


@router.get('/{event_id}', response_model=EventRead)
async def get_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service)
):
    try:
        event = await event_service.get_by_id(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
    return event


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


@router.patch(
    '/{event_id}/upgrade',
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)]
)
async def upgrade_event_status(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service),
):
    try:
        event = await event_service.upgrade_status(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
    except exceptions.UnexpectedEventStatus:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event already has finished')
    except exceptions.MatchesAreNotFinished:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='All matches should be finished')
    except exceptions.TooFewMatches:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Required min 5 matches')
    return event


@router.delete('/{event_id}', dependencies=[Depends(get_current_superuser)])
async def delete_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service)
):
    try:
        await event_service.delete(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
