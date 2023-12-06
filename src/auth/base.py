from typing import Sequence
from uuid import UUID

from src.auth.models import User
from src.auth.schemas import UserCreate, UserRead


class BaseAuthRepository:
    async def get_multiple(self) -> Sequence[User]:
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def create(self, new_user: UserCreate) -> User:
        raise NotImplementedError


class BaseAuthService:
    async def get_multiple(self) -> Sequence[UserRead]:
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> UserRead:
        raise NotImplementedError

    async def get_by_email(self, email: str) -> UserRead:
        raise NotImplementedError

    async def register(self, new_user: UserCreate) -> UserRead:
        raise NotImplementedError

    async def login(self, email: str, password: str) -> UserRead:
        raise NotImplementedError
