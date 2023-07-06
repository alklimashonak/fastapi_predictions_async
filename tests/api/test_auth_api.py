import logging
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.router import router as auth_router
from src.auth.service import get_auth_service
from tests.api.conftest import UserModel

logger = logging.getLogger(__name__)


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
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_auth_service] = fake_get_auth_service

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestLogin:
    async def test_get_access_token_valid_credentials(self, active_user: UserModel, async_client: AsyncClient):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': active_user.email,
            'password': 'user',
        }
        response = await async_client.post('/auth/login', data=data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['access_token']

    async def test_get_400_invalid_credentials(self, active_user: UserModel, async_client: AsyncClient):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': active_user.email,
            'password': 'wrong_password',
        }
        response = await async_client.post('/auth/login', data=data, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Incorrect email or password'
