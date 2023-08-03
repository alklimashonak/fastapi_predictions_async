import logging
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.predictions.router import router as prediction_router
from src.predictions.dependencies import get_prediction_service
from tests.api.conftest import UserModel, PredictionModel

logger = logging.getLogger(__name__)


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(prediction_router, prefix='', tags=['Predictions'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_current_user, fake_get_prediction_service
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_prediction_service] = fake_get_prediction_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestGetPredictions:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.get('/predictions/123')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_user_get_own_predictions(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
            superuser: UserModel,
    ) -> None:
        user_response = await async_client.get(
            '/predictions/123',
            headers={'Authorization': active_user.email}
        )

        superuser_response = await async_client.get(
            '/predictions/123',
            headers={'Authorization': superuser.email}
        )

        assert user_response.status_code == status.HTTP_200_OK
        assert superuser_response.status_code == status.HTTP_200_OK
        assert len(user_response.json()) == 1
        assert len(superuser_response.json()) == 1
        assert user_response.json()[0]['id'] != superuser_response.json()[0]['id']


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

    async def test_user_can_create_prediction(self, async_client: AsyncClient, active_user: UserModel) -> None:
        json = {
            'home_goals': 2,
            'away_goals': 2,
            'match_id': 1,
        }

        response = await async_client.post('/predictions', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['home_goals'] == json.get('home_goals')
        assert response.json()['away_goals'] == json.get('away_goals')
        assert response.json()['match_id'] == json.get('match_id')
        assert response.json()['user_id'] == str(active_user.id)


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

    async def test_prediction_doesnt_exist(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
    ) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/21321421412',
            json=json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Prediction not found'

    async def test_user_cant_update_other_users_prediction(
            self,
            async_client: AsyncClient,
            prediction1: PredictionModel,
            superuser: UserModel,
    ) -> None:
        json = {
            'home_goals': 5,
            'away_goals': 4,
        }

        response = await async_client.put(
            f'/predictions/{prediction1.id}',
            json=json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'You can only edit your own predictions'

    async def test_user_can_update_own_prediction(
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
