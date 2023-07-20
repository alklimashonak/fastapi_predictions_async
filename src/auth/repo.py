from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base import BaseAuthRepository
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.core.security import get_password_hash


class AuthRepository(BaseAuthRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_multiple(self) -> Sequence[User]:
        stmt = select(User)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).filter(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).filter(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, new_user: UserCreate) -> User:
        user = User(
            email=new_user.email,
            hashed_password=get_password_hash(new_user.password),
            is_active=True,
            is_superuser=False,
        )
        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)
        return user
