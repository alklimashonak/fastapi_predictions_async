from fastapi import APIRouter

from src.auth.config import fastapi_users, auth_backend
from src.auth.schemas import UserRead, UserCreate, UserUpdate

auth_router = APIRouter(prefix='/auth', tags=['Auth'])

auth_router.include_router(fastapi_users.get_auth_router(backend=auth_backend), prefix='/jwt')
auth_router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
auth_router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix='/users')
