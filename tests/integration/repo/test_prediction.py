import pytest

from sqlalchemy.exc import IntegrityError

from src.auth.models import User
from src.events.models import Event
from src.matches.models import Match
from src.matches.schemas import MatchRead
from src.predictions.base import BasePredictionRepository
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


@pytest.mark.asyncio
async def test_get_prediction_by_id(prediction_repo: BasePredictionRepository, test_prediction: Prediction) -> None:
    prediction = await prediction_repo.get_by_id(prediction_id=test_prediction.id)

    assert prediction.id == test_prediction.id
    assert prediction.home_goals == test_prediction.home_goals
    assert prediction.away_goals == test_prediction.away_goals
    assert prediction.points == test_prediction.points
    assert prediction.user_id == test_prediction.user_id
    assert prediction.match_id == test_prediction.match_id


@pytest.mark.asyncio
async def test_get_predictions_by_event_id(
        prediction_repo: BasePredictionRepository,
        test_prediction: Prediction,
        test_event: Event,
        test_user: User,
) -> None:
    predictions = await prediction_repo.get_multiple_by_event_id(event_id=test_event.id, user_id=test_user.id)

    assert len(predictions) == 1
    assert test_prediction.id == predictions[0].id


@pytest.mark.asyncio
async def test_unique_prediction(prediction_repo: BasePredictionRepository, test_match: Match, test_user: User) -> None:
    prediction = PredictionCreate(
        home_goals=1,
        away_goals=1,
        match_id=test_match.id,
    )

    with pytest.raises(IntegrityError):
        await prediction_repo.create(prediction=prediction, user_id=test_user.id)


@pytest.mark.asyncio
async def test_create_prediction(prediction_repo: BasePredictionRepository, another_match: Match,
                                 test_user: User) -> None:
    prediction = PredictionCreate(
        home_goals=1,
        away_goals=1,
        match_id=another_match.id,
    )

    db_prediction = await prediction_repo.create(prediction=prediction, user_id=test_user.id)

    assert db_prediction.id
    assert db_prediction.home_goals == prediction.home_goals
    assert db_prediction.away_goals == prediction.away_goals
    assert db_prediction.points is None
    assert db_prediction.user_id == test_user.id
    assert db_prediction.match_id == another_match.id


@pytest.mark.asyncio
async def test_update_prediction(prediction_repo: BasePredictionRepository, test_prediction: Prediction) -> None:
    data = PredictionUpdate(
        home_goals=5,
        away_goals=5,
    )

    updated_prediction = await prediction_repo.update(prediction_id=test_prediction.id, prediction=data)

    assert updated_prediction.id == test_prediction.id
    assert updated_prediction.home_goals == data.home_goals
    assert updated_prediction.away_goals == data.away_goals
    assert updated_prediction.user_id == test_prediction.user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'home_goals, away_goals, points',
    [
        (2, 2, 3),
        (0, 0, 1),
        (3, 3, 1),
        (1, 1, 1),
        (2, 0, 0),
        (0, 2, 0),
    ]
)
async def test_update_predictions_points(
        prediction_repo: BasePredictionRepository,
        test_prediction: Prediction,
        test_match: Match,
        home_goals: int,
        away_goals: int,
        points: int,
) -> None:
    assert test_prediction.points is None

    match = MatchRead(
        id=test_prediction.match_id,
        home_team=test_match.home_team,
        away_team=test_match.away_team,
        home_goals=home_goals,
        away_goals=away_goals,
        start_time=test_match.start_time,
        event_id=test_match.event_id,
        status=test_match.status,
    )

    await prediction_repo.update_points_for_match(match=match)

    updated_repo = await prediction_repo.get_by_id(prediction_id=test_prediction.id)

    assert updated_repo.points == points
