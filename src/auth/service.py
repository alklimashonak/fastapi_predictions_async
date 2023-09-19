import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from src.auth.base import BaseAuthService, BaseAuthRepository
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.core.security import verify_password

logger = logging.getLogger(__name__)


class AuthService(BaseAuthService):
    def __init__(self, repo: BaseAuthRepository):
        self.repo = repo

    async def get_multiple(self) -> Sequence[User]:
        return await self.repo.get_multiple()

    async def get_by_id(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id=user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email=email)

    async def register(self, new_user: UserCreate) -> User:
        user = await self.repo.get_by_email(email=new_user.email)

        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        return await self.repo.create(new_user=new_user)

    async def login(self, email: str, password: str) -> User | None:
        user = await self.repo.get_by_email(email=email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        return user
