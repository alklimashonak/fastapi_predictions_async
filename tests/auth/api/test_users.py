import pytest

from fastapi_users.router import ErrorCode
from httpx import AsyncClient

from src.auth.schemas import UserRead
from src.config import settings


class TestAuthRouterLogin:
    @pytest.mark.asyncio
    async def test_valid_login_returns_token(self, test_user: UserRead, client: AsyncClient):
        response = await client.post(
            '/auth/jwt/login',
            data={
                'username': test_user.email,
                'password': settings.TEST_USER_PASSWORD,
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        assert response.status_code == 200
        assert response.json()['access_token']

    @pytest.mark.asyncio
    async def test_invalid_login_raises_400(self, test_user: UserRead, client: AsyncClient):
        response = await client.post(
            '/auth/jwt/login',
            data={
                'username': test_user.email,
                'password': '123',
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        assert response.status_code == 400
        assert response.json()['detail'] == ErrorCode.LOGIN_BAD_CREDENTIALS


class TestAuthRouterRegister:
    @pytest.mark.asyncio
    async def test_valid_register_returns_user(self, client: AsyncClient):
        email = 'newtestuser@example.com'
        password = '1234'
        user_data = {
            'email': email,
            'password': password,
            'is_active': True,
            'is_superuser': False,
            'is_verified': False,
        }

        response = await client.post('/auth/register', json=user_data)

        assert response.status_code == 201
        assert response.json()['email'] == email

    @pytest.mark.asyncio
    async def test_register_the_same_email_failed(self, client: AsyncClient):
        user_data = {
            'email': 'newtestuser@example.com',
            'password': '1234',
            'is_active': True,
            'is_superuser': False,
            'is_verified': False,
        }

        response = await client.post('/auth/register', json=user_data)

        assert response.status_code == 400
        assert response.json()['detail'] == ErrorCode.REGISTER_USER_ALREADY_EXISTS


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get('/auth/users/me')

    assert response.status_code == 401
    assert response.json()['detail'] == 'Unauthorized'
