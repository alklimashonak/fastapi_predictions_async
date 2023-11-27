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
    '/{event_id}/run',
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)],
)
async def run_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service),
):
    try:
        event = await event_service.run(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
    except exceptions.EventAlreadyIsRunning:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event already is running')
    except exceptions.TooFewMatches:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Required min 5 matches')
    return event


@router.patch(
    '/{event_id}/start',
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)],
)
async def start_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service),
):
    try:
        event = await event_service.start(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
    except exceptions.EventAlreadyIsStarted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event already is started')
    return event


@router.patch(
    '/{event_id}/finish',
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)]
)
async def finish_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service),
):
    try:
        event = await event_service.finish(event_id=event_id)
    except exceptions.EventNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event not found')
    except exceptions.EventIsNotOngoing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event should have ongoing status')
    except exceptions.MatchesAreNotFinished:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='All matches should be finished')
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
