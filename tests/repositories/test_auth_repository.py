import pytest
from pydantic import EmailStr

from src.auth.models import User
from src.auth.base import BaseAuthRepository
from src.auth.schemas import UserCreate
from src.core.config import settings


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user(test_user: User, auth_repo: BaseAuthRepository) -> None:
    user = await auth_repo.get_by_id(user_id=test_user.id)

    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.is_superuser == test_user.is_superuser
    assert user.is_active == test_user.is_active
    assert user.hashed_password == test_user.hashed_password


@pytest.mark.asyncio
async def test_get_user_by_email_returns_user(test_user: User, auth_repo: BaseAuthRepository) -> None:
    user = await auth_repo.get_by_email(email=test_user.email)

    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.is_superuser == test_user.is_superuser
    assert user.is_active == test_user.is_active
    assert user.hashed_password == test_user.hashed_password


@pytest.mark.asyncio
async def test_create_user_works(auth_repo: BaseAuthRepository) -> None:
    user_email = 'new_user@example.com'

    data = UserCreate(
        email=EmailStr(user_email),
        password='some_pass',
    )

    new_user = await auth_repo.create(new_user=data)

    assert new_user.id
    assert new_user.email == user_email
    assert new_user.hashed_password
    assert new_user.is_active is True
    assert new_user.is_superuser is False


@pytest.mark.asyncio
@pytest.mark.skip
async def test_authenticate_returns_user_if_valid_data(auth_repo: BaseAuthRepository, test_user: User) -> None:
    user = await auth_repo.authenticate(test_user.email, settings.TEST_USER_PASSWORD)

    assert user.email == settings.TEST_USER_EMAIL


@pytest.mark.asyncio
@pytest.mark.skip
async def test_authenticate_returns_none_if_invalid_data(auth_repo: BaseAuthRepository, test_user: User) -> None:
    user = await auth_repo.authenticate(test_user.email, 'wrong_password')

    assert not user