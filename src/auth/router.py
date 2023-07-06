import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.base import BaseAuthService
from src.auth.schemas import Token, UserRead, UserCreate
from src.auth.service import get_auth_service
from src.core import security
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    auth_service: BaseAuthService = Depends(get_auth_service),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await auth_service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.email, expires_delta=access_token_expires),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserRead)
async def register(
    new_user: UserCreate,
    auth_service: BaseAuthService = Depends(get_auth_service),
):
    user = await auth_service.get_by_email(email=new_user.email)

    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    return await auth_service.create(new_user=new_user)


@router.get('/users', response_model=list[UserRead])
async def get_users(auth_service: BaseAuthService = Depends(get_auth_service)):
    return await auth_service.get_multiple()
