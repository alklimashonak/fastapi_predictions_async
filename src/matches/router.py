from fastapi import APIRouter, Depends
from fastapi.params import Query
from starlette import status

from src.auth.dependencies import get_current_superuser
from src.matches.base import BaseMatchService
from src.matches.dependencies import get_match_service
from src.matches.schemas import MatchRead, MatchCreate

router = APIRouter()


@router.post(
    '/events/{event_id}/matches',
    response_model=MatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_superuser)],
)
async def create_match(
        event_id: int,
        match: MatchCreate,
        match_service: BaseMatchService = Depends(get_match_service),
):
    return await match_service.create(match=match, event_id=event_id)


@router.delete(
    '/matches/{match_id}',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)],
)
async def delete_match(
        match_id: int,
        match_service: BaseMatchService = Depends(get_match_service),
):
    return await match_service.delete(match_id=match_id)


@router.patch(
    '/matches/{match_id}/finish',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_superuser)],
)
async def finish_match(
        match_id: int,
        home_goals: int = Query(ge=0, le=9),
        away_goals: int = Query(ge=0, le=9),
        match_service: BaseMatchService = Depends(get_match_service),
):
    return await match_service.finish(match_id=match_id, home_goals=home_goals, away_goals=away_goals)
