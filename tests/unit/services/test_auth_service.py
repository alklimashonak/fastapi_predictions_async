from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import EmailStr

from src import exceptions
from src.auth.base import BaseAuthRepository, BaseAuthService
from src.auth.schemas import UserRead, UserCreate
from src.auth.service import AuthService
from tests.utils import UserModel, user_password


@pytest.fixture
def auth_service(mock_auth_repo: BaseAuthRepository) -> BaseAuthService:
    yield AuthService(mock_auth_repo)


@pytest.mark.asyncio
class TestGetMultiple:
    async def test_get_multiple_users(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
            superuser: UserModel,
    ) -> None:
        users = await auth_service.get_multiple()

        assert UserRead.from_orm(active_user) in users
        assert UserRead.from_orm(superuser) in users


@pytest.mark.asyncio
class TestGetByID:
    async def test_get_not_existing_user(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        with pytest.raises(HTTPException):
            await auth_service.get_by_id(user_id=uuid4())

    async def test_get_existing_user(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = await auth_service.get_by_id(user_id=active_user.id)

        assert UserRead.from_orm(active_user) == user


@pytest.mark.asyncio
class TestRegister:
    async def test_user_already_exists(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user_data = UserCreate(
            email=EmailStr(active_user.email),
            password='1234',
        )

        with pytest.raises(exceptions.UserAlreadyExists):
            await auth_service.register(new_user=user_data)

    async def test_user_registered_successfully(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        user_data = UserCreate(
            email=EmailStr('new_user@gmail.com'),
            password='1234',
        )

        user = await auth_service.register(new_user=user_data)

        assert type(user) == UserRead
        assert user.email == user.email
        assert user.is_active is True
        assert user.is_superuser is False


@pytest.mark.asyncio
class TestLogin:
    async def test_user_not_existing(
            self,
            auth_service: BaseAuthService,
    ) -> None:
        with pytest.raises(exceptions.InvalidEmailOrPassword):
            await auth_service.login(email='not_existing@gmail.com', password='1234')

    async def test_invalid_password(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        with pytest.raises(exceptions.InvalidEmailOrPassword):
            await auth_service.login(email=active_user.email, password='324324223')

    async def test_successfully_logged(
            self,
            auth_service: BaseAuthService,
            active_user: UserModel,
    ) -> None:
        user = await auth_service.login(email=active_user.email, password=user_password)

        assert UserRead.from_orm(active_user) == user
