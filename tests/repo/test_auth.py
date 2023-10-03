import pytest
from pydantic import EmailStr

from src.auth.base import BaseAuthRepository
from src.auth.models import User
from src.auth.schemas import UserCreate


@pytest.mark.asyncio
async def test_get_user_by_id(auth_repo: BaseAuthRepository, test_user: User) -> None:
    user = await auth_repo.get_by_id(user_id=test_user.id)

    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_email(auth_repo: BaseAuthRepository, test_user: User) -> None:
    user = await auth_repo.get_by_email(email=test_user.email)

    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_create_user(auth_repo: BaseAuthRepository) -> None:
    user_data = UserCreate(
        email=EmailStr('test_user2@test.com'),
        password='1234',
    )

    user = await auth_repo.create(new_user=user_data)

    assert user.id
    assert user.email == user_data.email
    assert user.hashed_password != user_data.password
    assert user.is_active is True
    assert user.is_superuser is False
