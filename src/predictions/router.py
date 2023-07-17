from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserRead
from src.predictions.base import BasePredictionService
from src.predictions.schemas import PredictionRead, PredictionCreate, PredictionUpdate
from src.predictions.service import get_prediction_service

router = APIRouter()


@router.get('/events/{event_id}/predictions', response_model=list[PredictionRead])
async def get_predictions(
        event_id: int,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: BasePredictionService = Depends(get_prediction_service),
):
    return await prediction_service.get_multiple_by_event_id(event_id=event_id, user_id=current_user.id)


@router.post('/predictions', response_model=PredictionRead)
async def create_prediction(
        prediction: PredictionCreate,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: BasePredictionService = Depends(get_prediction_service),
):
    return await prediction_service.create(prediction=prediction, user_id=current_user.id)


@router.put('/predictions/{prediction_id}', response_model=PredictionRead)
async def update_prediction(
        prediction_id: int,
        prediction: PredictionUpdate,
        current_user: UserRead = Depends(get_current_user),
        prediction_service: BasePredictionService = Depends(get_prediction_service),
):
    prediction_to_update = await prediction_service.get_by_id(prediction_id=prediction_id)

    if prediction_to_update.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You can only edit your own predictions')

    return await prediction_service.update(prediction_id=prediction_id, prediction=prediction)
