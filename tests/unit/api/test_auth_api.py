from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_auth_service
from src.auth.router import router as auth_router
from tests.utils import UserModel, user_password


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(auth_router, prefix='/auth', tags=['Auth'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_auth_service
) -> AsyncGenerator[AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_auth_service] = fake_get_auth_service

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestLogin:
    async def test_valid_credentials(
            self, active_user: UserModel, async_client: AsyncClient
    ) -> None:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': active_user.email,
            'password': user_password,
        }
        response = await async_client.post('/auth/login', data=data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get('access_token') is not None
        assert response.json().get('token_type') == 'bearer'

    async def test_wrong_password(
            self, active_user: UserModel, async_client: AsyncClient
    ) -> None:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': active_user.email,
            'password': 'wrong_password',
        }
        response = await async_client.post('/auth/login', data=data, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get('detail') == 'Invalid email or password'

    async def test_blank_credentials(
            self, active_user: UserModel, async_client: AsyncClient
    ) -> None:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {}
        response = await async_client.post('/auth/login', data=data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestRegister:
    async def test_user_already_exists(
            self, active_user: UserModel, async_client: AsyncClient
    ) -> None:
        user_data = {
            'email': active_user.email,
            'password': 'some_password',
        }

        response = await async_client.post('/auth/register', json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'User with this email already exists in the system.'

    @pytest.mark.parametrize(
        'email, status_code',
        [
            ('validemail@example.com', status.HTTP_200_OK),
            ('invalid_email', status.HTTP_422_UNPROCESSABLE_ENTITY),
        ]
    )
    async def test_email_validity(
            self, active_user: UserModel, async_client: AsyncClient, email: str, status_code: int) -> None:
        user_data = {
            'email': email,
            'password': 'some_password',
        }

        response = await async_client.post('/auth/register', json=user_data)

        assert response.status_code == status_code

    async def test_valid_data(self, async_client: AsyncClient) -> None:
        new_user_email = 'newuser@example.com'
        user_data = {
            'email': new_user_email,
            'password': 'password'
        }

        response = await async_client.post('/auth/register', json=user_data)

        assert response.json()['id'] is not None
        assert response.json()['email'] == new_user_email
        assert response.json().get('password') is None
        assert response.json()['is_active'] is True
        assert response.json()['is_superuser'] is False
