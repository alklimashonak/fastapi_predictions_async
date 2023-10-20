import logging
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.events.models import EventStatus
from src.events.router import router as event_router
from src.events.dependencies import get_event_service
from tests.api.conftest import UserModel
from tests.utils import EventModel

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
    async def test_get_event_works(self, async_client: AsyncClient, event1: EventModel) -> None:
        response = await async_client.get(f'/events/{event1.id}')

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
        assert response.json()['name'] == self.json.get('name')


@pytest.mark.asyncio
class TestUpdateEvent:
    async def test_missing_token(self, async_client: AsyncClient, event1: EventModel) -> None:
        response = await async_client.patch(f'/events/{event1.id}/run')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel, event1: EventModel) -> None:
        response = await async_client.patch(f'/events/{event1.id}/run', headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.patch('/events/99999/run', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'

    async def test_event_already_started(self, async_client: AsyncClient,
                                         superuser: UserModel, active_event: EventModel) -> None:
        response = await async_client.patch(
            f'/events/{active_event.id}/run',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'You can run only not started events'

    async def test_can_not_finish_upcoming_event(
            self,
            async_client: AsyncClient,
            superuser: UserModel,
            active_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{active_event.id}/finish?home_goals=5&away_goals=6',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Event should have ongoing status'

    async def test_can_finish_ready_event(
            self,
            async_client: AsyncClient,
            superuser: UserModel,
            ready_to_finish_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{ready_to_finish_event.id}/finish',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == EventStatus.completed

    async def test_superuser_has_access(self, async_client: AsyncClient,
                                        superuser: UserModel, event1: EventModel) -> None:
        response = await async_client.patch(
            f'/events/{event1.id}/run',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 1


@pytest.mark.asyncio
class TestDeleteEvent:
    async def test_missing_token(self, async_client: AsyncClient, event1: EventModel) -> None:
        response = await async_client.delete(f'/events/{event1.id}')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_forbidden(self, async_client: AsyncClient, active_user: UserModel, event1: EventModel) -> None:
        response = await async_client.delete(f'/events/{event1.id}', headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/events/99999', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'

    async def test_superuser_has_access(self, async_client: AsyncClient,
                                        superuser: UserModel, event1: EventModel) -> None:
        response = await async_client.delete(f'/events/{event1.id}', headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_200_OK
