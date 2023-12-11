from typing import AsyncGenerator, cast, Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.events.dependencies import get_event_service
from src.events.models import EventStatus
from src.events.router import router as event_router
from tests.utils import EventModel, UserModel


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
) -> AsyncGenerator[AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_event_service] = fake_get_event_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestGetEvents:
    async def test_get_events_without_admin_mode(
            self,
            async_client: AsyncClient,
            created_event: EventModel,
            upcoming_event: EventModel,
    ) -> None:
        response = await async_client.get('/events')
        data = cast(list[dict[str, Any]], response.json())

        event_ids = [event['id'] for event in data]

        assert response.status_code == 200
        assert created_event.id not in event_ids
        assert upcoming_event.id in event_ids

    async def test_get_events_with_admin_mode(
            self,
            async_client: AsyncClient,
            created_event: EventModel,
            upcoming_event: EventModel,
    ) -> None:
        response = await async_client.get('/events?admin_mode=true')
        data = cast(list[dict[str, Any]], response.json())

        event_ids = [event['id'] for event in data]

        assert response.status_code == 200
        assert created_event.id in event_ids
        assert upcoming_event.id in event_ids
        assert data[0].get('matches') is None


@pytest.mark.asyncio
class TestGetByID:
    async def test_event_not_found(
            self,
            async_client: AsyncClient,
    ) -> None:
        response = await async_client.get('/events/987')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_upcoming_event(
            self,
            async_client: AsyncClient,
            upcoming_event: EventModel,
            created_event: EventModel,
    ) -> None:
        response = await async_client.get(f'/events/{upcoming_event.id}')

        data = cast(dict[str, Any], response.json())

        assert data['id'] == upcoming_event.id
        assert data['name'] == upcoming_event.name


@pytest.mark.asyncio
class TestCreateEvent:
    async def test_missing_token(
            self,
            async_client: AsyncClient,
    ) -> None:
        json = {
            'name': 'Event 1',
            'deadline': '2023-09-20 10:27:21.240752',
        }

        response = await async_client.post('/events', json=json)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
    ) -> None:
        json = {
            'name': 'Event 1',
            'deadline': '2023-09-20 10:27:21.240752',
        }

        response = await async_client.post('/events', json=json, headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == "The user doesn't have enough privileges"

    async def test_superuser_has_access(
            self,
            async_client: AsyncClient,
            superuser: UserModel,
    ) -> None:
        json = {
            'name': 'Event 1',
            'deadline': '2023-09-20 10:27:21.240752',
        }

        response = await async_client.post('/events', json=json, headers={'Authorization': superuser.email})

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
class TestUpgradeEventStatus:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.patch('/events/123/upgrade')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self, async_client: AsyncClient, active_user: UserModel, created_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{created_event.id}/upgrade', headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == "The user doesn't have enough privileges"

    async def test_event_not_found(
            self, async_client: AsyncClient, superuser: UserModel
    ) -> None:
        response = await async_client.patch(
            '/events/987/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Event not found'

    async def test_upgrade_completed_event(
            self, async_client: AsyncClient, superuser: UserModel, completed_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{completed_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Event already has finished'

    async def test_upgrade_closed_event_that_has_uncompleted_matches(
            self, async_client: AsyncClient, superuser: UserModel, closed_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{closed_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'All matches should be finished'

    async def test_upgrade_created_event_without_matches(
            self, async_client: AsyncClient, superuser: UserModel, event_without_matches: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{event_without_matches.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Required min 5 matches'

    async def test_upgrade_created_event_with_matches(
            self, async_client: AsyncClient, superuser: UserModel, created_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{created_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == EventStatus.upcoming

    async def test_upgrade_upcoming_event(
            self, async_client: AsyncClient, superuser: UserModel, upcoming_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{upcoming_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == EventStatus.ongoing

    async def test_upgrade_ongoing_event(
            self, async_client: AsyncClient, superuser: UserModel, ongoing_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{ongoing_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == EventStatus.closed

    async def test_upgrade_closed_event_with_completed_matches(
            self, async_client: AsyncClient, superuser: UserModel, ready_to_finish_event: EventModel
    ) -> None:
        response = await async_client.patch(
            f'/events/{ready_to_finish_event.id}/upgrade', headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == EventStatus.completed


@pytest.mark.asyncio
class TestDeleteEvent:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.delete('/events/123')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self, async_client: AsyncClient, active_user: UserModel
    ) -> None:
        response = await async_client.delete('/events/123', headers={'Authorization': active_user.email})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == "The user doesn't have enough privileges"

    async def test_superuser_has_access(
            self, async_client: AsyncClient, superuser: UserModel
    ) -> None:
        response = await async_client.delete(
            '/events/123',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_event_not_found(
            self, async_client: AsyncClient, superuser: UserModel
    ) -> None:
        response = await async_client.delete(
            '/events/987',
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
