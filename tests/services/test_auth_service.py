from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import EmailStr

from src.auth.base import BaseAuthService, BaseAuthRepository
from src.auth.schemas import UserCreate
from src.auth.service import AuthService
from tests.services.conftest import UserModel, user_password


@pytest.fixture
def auth_service(mock_auth_repo: BaseAuthRepository) -> BaseAuthService:
    yield AuthService(mock_auth_repo)


@pytest.mark.asyncio
class TestGetMultiple:
    async def test_get_multiple_users_works(self, auth_service: BaseAuthService) -> None:
        users = await auth_service.get_multiple()

        assert len(users) == 2


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_existent_user_returns_user(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = await auth_service.get_by_id(user_id=active_user.id)

        assert user
        assert user.id == active_user.id

    async def test_get_not_existent_user_raises_http_exc(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        with pytest.raises(HTTPException):
            await auth_service.get_by_id(user_id=uuid4())


@pytest.mark.asyncio
class TestGetByEmail:
    async def test_get_existent_user_returns_user(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = await auth_service.get_by_email(email=active_user.email)

        assert user
        assert user.id == active_user.id
        assert user.email == active_user.email

    async def test_get_not_existent_user_returns_none(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        user = await auth_service.get_by_email(email='not_existed_email@domen.com')

        assert not user


@pytest.mark.asyncio
class TestRegister:
    async def test_register_works(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        user_email = EmailStr('validemail@domen.com')

        user = UserCreate(
            email=user_email,
            password='1234',
        )
        user = await auth_service.register(new_user=user)

        assert user.id
        assert user.hashed_password
        assert user.email == user_email
        assert user.is_active is True
        assert user.is_superuser is False

    async def test_register_with_existed_email_raises_http_exc(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = UserCreate(
            email=EmailStr(active_user.email),
            password='1234',
        )

        with pytest.raises(HTTPException):
            await auth_service.register(new_user=user)


@pytest.mark.asyncio
class TestLogin:
    async def test_valid_login_returns_user(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = await auth_service.login(email=active_user.email, password=user_password)

        assert user.id
        assert user.email == active_user.email

    async def test_not_existed_email_raises_http_exc(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        with pytest.raises(HTTPException):
            await auth_service.login(email='not_existed_email@domen.com', password='1234')

    async def test_incorrect_password_raises_http_exc(
            self,
            auth_service: BaseAuthService,
            active_user,
    ) -> None:
        with pytest.raises(HTTPException):
            await auth_service.login(email=active_user.email, password='incorrect')
