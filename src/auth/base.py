from pydantic import UUID4

from src.auth.models import User
from src.auth.schemas import UserCreate


class BaseAuthService:
    async def get_multiple(self) -> list[User]:
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID4) -> User | None:
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def create(self, new_user: UserCreate) -> User | None:
        raise NotImplementedError

    async def authenticate(self, email: str, password: str) -> User | None:
        raise NotImplementedError
