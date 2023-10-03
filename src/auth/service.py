import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from src.auth.base import BaseAuthService, BaseAuthRepository
from src.auth.schemas import UserCreate, UserRead
from src.core.security import verify_password

logger = logging.getLogger(__name__)


class AuthService(BaseAuthService):
    def __init__(self, repo: BaseAuthRepository):
        self.repo = repo

    async def get_multiple(self) -> Sequence[UserRead]:
        users = await self.repo.get_multiple()

        return [UserRead.from_orm(user) for user in users]

    async def get_by_id(self, user_id: UUID) -> UserRead:
        user = await self.repo.get_by_id(user_id=user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
        return UserRead.from_orm(user)

    async def get_by_email(self, email: str) -> UserRead:
        return await self.repo.get_by_email(email=email)

    async def register(self, new_user: UserCreate) -> UserRead:
        user = await self.repo.get_by_email(email=new_user.email)

        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        user = await self.repo.create(new_user=new_user)

        return UserRead.from_orm(user)

    async def login(self, email: str, password: str) -> UserRead:
        user = await self.repo.get_by_email(email=email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        return UserRead.from_orm(user)
