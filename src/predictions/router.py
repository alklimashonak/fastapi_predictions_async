from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src import exceptions
from src.auth.dependencies import get_current_user
from src.auth.schemas import UserRead
from src.predictions.base import BasePredictionService
from src.predictions.dependencies import get_prediction_service
from src.predictions.schemas import PredictionRead, PredictionCreate, PredictionUpdate
from src.predictions.service import PredictionService

router = APIRouter()


@router.get('/{event_id}', response_model=list[PredictionRead])
async def get_predictions(
        event_id: int,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: PredictionService = Depends(get_prediction_service),
):
    return await prediction_service.get_multiple_by_event_id(event_id=event_id, user_id=current_user.id)


@router.post('', response_model=PredictionRead, status_code=status.HTTP_201_CREATED)
async def create_prediction(
        prediction: PredictionCreate,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: BasePredictionService = Depends(get_prediction_service),
):
    try:
        new_prediction = await prediction_service.create(prediction=prediction, user_id=current_user.id)
    except exceptions.MatchNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Match not found')
    except (exceptions.MatchAlreadyIsRunning, exceptions.MatchAlreadyIsCompleted):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The match has already started')
    except exceptions.PredictionAlreadyExists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Prediction for this match already exists')
    return new_prediction


@router.put('/{prediction_id}', response_model=PredictionRead)
async def update_prediction(
        prediction_id: int,
        prediction: PredictionUpdate,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: PredictionService = Depends(get_prediction_service),
):
    try:
        prediction = await prediction_service.update(
            prediction_id=prediction_id, prediction=prediction, user_id=current_user.id
        )
    except exceptions.PredictionNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Prediction not found')
    except exceptions.UserIsNotAllowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You can only edit your own predictions')
    except (exceptions.MatchAlreadyIsRunning, exceptions.MatchAlreadyIsCompleted):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The match has already started')
    return prediction
