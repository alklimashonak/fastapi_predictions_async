import logging

from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.base import BaseAuthService
from src.auth.repo import AuthRepository
from src.auth.schemas import TokenPayload, UserRead
from src.auth.service import AuthService
from src.core.config import settings
from src.core.security import oauth2_scheme, ALGORITHM
from src.db.database import get_async_session

logger = logging.getLogger(__name__)


async def get_auth_repo(session: AsyncSession = Depends(get_async_session)):
    yield AuthRepository(session)


async def get_auth_service(repo: AuthRepository = Depends(get_auth_repo)):
    yield AuthService(repo)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        auth_service: BaseAuthService = Depends(get_auth_service),
) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exception
    user = await auth_service.get_by_email(email=token_data.sub)
    logger.warning(token_data.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_superuser(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
