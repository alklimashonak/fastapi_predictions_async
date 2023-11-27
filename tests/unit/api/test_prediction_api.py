from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.matches.models import MatchStatus
from src.predictions.dependencies import get_prediction_service
from src.predictions.router import router as prediction_router
from tests.utils import PredictionModel, UserModel, EventModel, MatchModel


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(prediction_router, prefix='/predictions', tags=['Predictions'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_current_user, fake_get_prediction_service
) -> AsyncGenerator[AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_prediction_service] = fake_get_prediction_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestGetPredictions:
    async def test_missing_token(self, async_client: AsyncClient, prediction1: PredictionModel) -> None:
        response = await async_client.get(f'/predictions/{prediction1.id}')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_user_get_own_predictions(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
            superuser: UserModel,
            prediction1: PredictionModel,
            ongoing_event: EventModel,
    ) -> None:
        user_response = await async_client.get(
            f'/predictions/{ongoing_event.id}',
            headers={'Authorization': active_user.email}
        )

        superuser_response = await async_client.get(
            f'/predictions/{ongoing_event.id}',
            headers={'Authorization': superuser.email}
        )

        assert user_response.status_code == status.HTTP_200_OK
        assert superuser_response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestCreatePrediction:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': 1,
        }

        response = await async_client.post('/predictions', json=json)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_missing_data(self, async_client: AsyncClient, active_user: UserModel) -> None:
        response = await async_client.post('/predictions', headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_valid_data(
            self, async_client: AsyncClient, active_user: UserModel, upcoming_match2: MatchModel
    ) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': upcoming_match2.id,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['home_goals'] == json.get('home_goals')
        assert response.json()['away_goals'] == json.get('away_goals')
        assert response.json()['match_id'] == json.get('match_id')
        assert response.json()['user_id'] == str(active_user.id)

    async def test_match_not_found(self, async_client: AsyncClient, active_user: UserModel) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': 987,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Match not found'

    async def test_prediction_already_exists(
            self, async_client: AsyncClient, prediction1: PredictionModel, active_user: UserModel
    ) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': prediction1.match_id,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Prediction for this match already exists'

    async def test_create_prediction_for_ongoing_match(
            self, async_client: AsyncClient, active_user: UserModel, ongoing_match: MatchModel
    ) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': ongoing_match.id,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'The match has already started'

    async def test_create_prediction_for_completed_match(
            self, async_client: AsyncClient, active_user: UserModel, completed_match: MatchModel
    ) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': completed_match.id,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'The match has already started'


@pytest.mark.asyncio
class TestUpdatePrediction:
    async def test_missing_token(self, async_client: AsyncClient, prediction1: PredictionModel) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(f'/predictions/{prediction1.id}', json=json)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_missing_data(
            self,
            async_client: AsyncClient,
            prediction1: PredictionModel,
            active_user: UserModel
    ) -> None:
        response = await async_client.put(
            f'/predictions/{prediction1.id}',
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_valid_data(
            self,
            async_client: AsyncClient,
            prediction1: PredictionModel,
            active_user: UserModel,
    ) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/{prediction1.id}',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_prediction_not_found(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
    ) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            '/predictions/987',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Prediction not found'

    async def test_user_try_to_update_not_own_prediction(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
            prediction2: PredictionModel,
    ) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/{prediction2.id}',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'You can only edit your own predictions'

    async def test_update_prediction_for_ongoing_match(
            self,
            async_client: AsyncClient,
            prediction1: PredictionModel,
            active_user: UserModel,
            upcoming_match: MatchModel,
    ) -> None:
        upcoming_match.status = MatchStatus.ongoing

        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/{prediction1.id}',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'The match has already started'

    async def test_update_prediction_for_completed_match(
            self,
            async_client: AsyncClient,
            prediction1: PredictionModel,
            active_user: UserModel,
            upcoming_match: MatchModel,
    ) -> None:
        upcoming_match.status = MatchStatus.completed

        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/{prediction1.id}',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'The match has already started'
