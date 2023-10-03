import logging
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.matches.dependencies import get_match_service
from src.matches.router import router as match_router
from tests.api.conftest import UserModel
from tests.utils import EventModel, MatchModel

logger = logging.getLogger(__name__)


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(match_router, prefix='', tags=['Matches'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_current_user, fake_get_match_service
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_match_service] = fake_get_match_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestCreateMatch:
    json = {
        'home_team': 'Atalanta',
        'away_team': 'Bari',
        'start_time': '2023-09-20 10:27:21.240752',
    }

    async def test_missing_token(self, async_client: AsyncClient, event1: EventModel) -> None:
        response = await async_client.post(
            f'/events/{event1.id}/matches',
            json=self.json
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel, event1: EventModel) -> None:
        response = await async_client.post(
            f'/events/{event1.id}/matches',
            json=self.json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(self, async_client: AsyncClient,
                                        superuser: UserModel, event1: EventModel) -> None:
        response = await async_client.post(
            f'/events/{event1.id}/matches',
            json=self.json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['home_team'] == self.json.get('home_team')

    async def test_too_short_team_name_raises_422(self, async_client: AsyncClient,
                                                  superuser: UserModel, event1: EventModel) -> None:
        invalid_data = {
            'home_team': '',
            'away_team': '',
            'start_data': '2023-09-20 10:27:21.240752',
        }

        response = await async_client.post(
            f'/events/{event1.id}/matches',
            json=invalid_data,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestDeleteMatch:
    async def test_missing_token(self, async_client: AsyncClient, match1: MatchModel) -> None:
        response = await async_client.delete(
            f'/matches/{match1.id}',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel, match1: MatchModel) -> None:
        response = await async_client.delete(
            f'/matches/{match1.id}',
            headers={'Authorization': active_user.email},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_match_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/matches/99999', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Match not found'

    async def test_superuser_has_access(self, async_client: AsyncClient,
                                        superuser: UserModel, match1: MatchModel) -> None:
        response = await async_client.delete(
            f'/matches/{match1.id}',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
