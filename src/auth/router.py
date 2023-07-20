import logging
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import Token, UserRead, UserCreate
from src.auth.dependencies import get_auth_service
from src.auth.service import AuthService
from src.core import security
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    auth_service: AuthService = Depends(get_auth_service),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await auth_service.login(email=form_data.username, password=form_data.password)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.email, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserRead)
async def register(
    new_user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.register(new_user=new_user)


@router.get('/users', response_model=list[UserRead])
async def get_users(auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.get_multiple()
