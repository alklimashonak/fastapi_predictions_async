from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi_users.authentication import Authenticator
from httpx import AsyncClient
from starlette import status

from src.events.dependencies import get_event_db
from src.events.router import get_events_router
from tests.api.conftest import get_mock_authentication, override_get_event_db, UserModel


@pytest.fixture
def app_factory(get_user_manager, mock_authentication):
    def _app_factory() -> FastAPI:
        mock_authentication_bis = get_mock_authentication(name="mock-bis")
        authenticator = Authenticator(
            [mock_authentication, mock_authentication_bis], get_user_manager
        )

        event_router = get_events_router(authenticator=authenticator)

        app = FastAPI()
        app.include_router(event_router)

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_event_db] = override_get_event_db

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestGetEvents:
    async def test_get_events_api_works(self, async_client: AsyncClient) -> None:
        response = await async_client.get('/events')

        assert response.status_code == 200


@pytest.mark.asyncio
class TestGetEvent:
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
        'status': 0,
        'start_time': '2023-09-20 10:27:21.240752',
        'matches': [
            {
                'team1': 'team1',
                'team2': 'team2',
                'status': 0,
                'start_time': '2023-09-20 10:27:21.240752',
                'team1_goals': None,
                'team2_goals': None,
            }
        ]
    }

    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            '/events',
            json=self.json
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_forbidden(self, async_client: AsyncClient, user: UserModel) -> None:
        response = await async_client.post(
            '/events',
            json=self.json,
            headers={'Authorization': f'Bearer {user.id}'}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.post(
            '/events',
            json=self.json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == 'Event 1'


@pytest.mark.asyncio
class TestUpdateEvent:
    json = {
        'name': 'Event 2',
        'status': 1,
        'start_time': '2023-09-20 10:27:21.240752',
        'new_matches': [],
    }

    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.put(
            '/events/123',
            json=self.json
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_name(self, async_client: AsyncClient, superuser: UserModel) -> None:
        data = {k: v for k, v in self.json.items() if k != 'name'}

        response = await async_client.put(
            '/events/123',
            json=data,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()['detail'][0]['msg'] == 'field required'

    async def test_empty_start_time(self, async_client: AsyncClient, superuser: UserModel) -> None:
        data = {k: v for k, v in self.json.items()}
        data['start_time'] = ''

        response = await async_client.put(
            '/events/123',
            json=data,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()['detail'][0]['msg'] == 'invalid datetime format'

    async def test_forbidden(self, async_client: AsyncClient, user: UserModel) -> None:
        response = await async_client.put(
            '/events/123',
            json=self.json,
            headers={'Authorization': f'Bearer {user.id}'}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.put(
            '/events/123',
            json=self.json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Event 2'

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.put(
            '/events/99999',
            json=self.json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'

    async def test_add_match(self, async_client: AsyncClient, superuser: UserModel) -> None:
        json = {k: v for k, v in self.json.items()}
        json['new_matches'] = [
            {
                'team1': 'team3',
                'team2': 'team4',
                'status': 0,
                'start_time': '2023-09-20 10:27:21.240752',
                'team1_goals': None,
                'team2_goals': None,
            }
        ]
        response = await async_client.put(
            '/events/123',
            json=json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['matches']) == 2

    async def test_update_match(self, async_client: AsyncClient, superuser: UserModel) -> None:
        json = {k: v for k, v in self.json.items()}
        json['matches_to_update'] = [
            {
                'id': 123,
                'team1': 'team3',
                'team2': 'team4',
                'status': 0,
                'start_time': '2023-09-20 10:27:21.240752',
                'team1_goals': None,
                'team2_goals': None,
            }
        ]
        response = await async_client.put(
            '/events/123',
            json=json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['matches']) == 1
        assert response.json()['matches'][0]['team1'] == 'team3'

    async def test_remove_match(self, async_client: AsyncClient, superuser: UserModel) -> None:
        json = {k: v for k, v in self.json.items()}
        json['matches_to_delete'] = [123]
        response = await async_client.put(
            '/events/123',
            json=json,
            headers={'Authorization': f'Bearer {superuser.id}'}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['matches']) == 0


@pytest.mark.asyncio
class TestDeleteEvent:
    async def test_missing_token(self, async_client: AsyncClient) -> None:
        response = await async_client.delete('/events/123')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_forbidden(self, async_client: AsyncClient, user: UserModel) -> None:
        response = await async_client.delete('/events/123', headers={'Authorization': f'Bearer {user.id}'})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/events/99999', headers={'Authorization': f'Bearer {superuser.id}'})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'event not found'

    async def test_superuser_has_access(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete('/events/123', headers={'Authorization': f'Bearer {superuser.id}'})

        assert response.status_code == status.HTTP_200_OK
