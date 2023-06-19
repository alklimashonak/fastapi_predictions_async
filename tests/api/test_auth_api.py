from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from fastapi_users.authentication import Authenticator
from fastapi_users.router import get_users_router

from tests.api.conftest import get_mock_authentication, User, UserUpdate, UserModel
from src.events.router import get_events_router


@pytest.fixture
def app_factory(get_user_manager, mock_authentication):
    def _app_factory(requires_verification: bool) -> FastAPI:
        mock_authentication_bis = get_mock_authentication(name="mock-bis")
        authenticator = Authenticator(
            [mock_authentication, mock_authentication_bis], get_user_manager
        )

        user_router = get_users_router(
            get_user_manager,
            User,
            UserUpdate,
            authenticator,
            requires_verification=requires_verification,
        )

        event_router = get_events_router(authenticator=authenticator)

        app = FastAPI()
        app.include_router(user_router)
        app.include_router(event_router)

        return app

    return _app_factory


@pytest_asyncio.fixture
async def test_app_client(
    get_test_client, app_factory
) -> AsyncGenerator[httpx.AsyncClient, None]:

    app = app_factory(requires_verification=True)

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
async def test_active_user(
    test_app_client: httpx.AsyncClient,
    user: UserModel,
):
    client = test_app_client
    response = await client.get(
        "/me", headers={"Authorization": f"Bearer {user.id}"}
    )

    assert response.status_code == 403
