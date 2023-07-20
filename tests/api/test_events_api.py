import logging
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.events.router import router as event_router
from src.events.dependencies import get_event_service
from tests.api.conftest import UserModel

logger = logging.getLogger(__name__)


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(event_router, prefix='/events', tags=['Events'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_current_user, fake_get_event_service
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_event_service] = fake_get_event_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestGetEvents:
    async def test_get_events_api_works(self, async_client: AsyncClient) -> None:
        response = await async_client.get('/events')

        assert response.status_code == 200


@pytest.mark.asyncio
class TestGetEventByID:
    async def test_get_event_works(self, async_client: AsyncClient) -> None:
        response = await async_client.get('/events/123')

        assert response.status_code == status.HTTP_200_OK

    async def test_event_not_found(self, async_client: AsyncClient) -> None:
        response = await async_client.get('/events/99999')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'


@pytest.mark.asyncio
class TestCreateEvent:
    json = {
        'name': 'Event 1',
        'deadline': '2023-09-20 10:27:21.240752',
    }

    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            '/events',
            json=self.json
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel) -> None:
        response = await async_client.post(
            '/events',
            json=self.json,
            headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.post(
            '/events',
            json=self.json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == 'Event 1'


@pytest.mark.asyncio
class TestDeleteEvent:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.delete('/events/123')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel) -> None:
        response = await async_client.delete('/events/123', headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/events/99999', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'

    async def test_superuser_has_access(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/events/123', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_200_OK
