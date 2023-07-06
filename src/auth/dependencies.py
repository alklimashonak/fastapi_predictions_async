import logging

from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from starlette import status

from src.auth.base import BaseAuthService
from src.auth.models import User
from src.auth.schemas import TokenPayload
from src.auth.service import get_auth_service
from src.core.config import settings
from src.core.security import oauth2_scheme, ALGORITHM

logger = logging.getLogger(__name__)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        auth_service: BaseAuthService = Depends(get_auth_service),
) -> User:
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
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
