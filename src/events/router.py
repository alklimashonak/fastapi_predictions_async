from fastapi import APIRouter, Depends
from starlette import status

from src.auth.dependencies import get_current_superuser
from src.events.base import BaseEventService
from src.events.dependencies import get_event_service
from src.events.schemas import EventRead, EventCreate, MatchCreate, MatchRead

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
    return await event_service.run(event_id=event_id)


@router.delete('/{event_id}', dependencies=[Depends(get_current_superuser)])
async def delete_event(
        event_id: int,
        event_service: BaseEventService = Depends(get_event_service)
):
    return await event_service.delete(event_id=event_id)


@router.post(
    '/{event_id}/matches',
    response_model=MatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_superuser)],
)
async def create_match(
        event_id: int,
        match: MatchCreate,
        event_service: BaseEventService = Depends(get_event_service),
):
    return await event_service.create_match(match=match, event_id=event_id)


@router.delete(
    '/matches/{match_id}',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)],
)
async def delete_match(
        match_id: int,
        event_service: BaseEventService = Depends(get_event_service),
):
    return await event_service.delete_match_by_id(match_id=match_id)
