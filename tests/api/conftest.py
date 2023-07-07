import dataclasses
import random
import uuid
from datetime import datetime
from typing import AsyncGenerator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import OAuth2
from pydantic import UUID4
from starlette import status

from src.auth.base import BaseAuthService
from src.auth.schemas import UserCreate
from src.core.security import get_password_hash, verify_password
from src.events.base import BaseEventService
from src.events.models import Status
from src.events.schemas import EventCreate


user_password = 'user'
superuser_password = 'admin'
user_password_hash = get_password_hash(user_password)
superuser_password_hash = get_password_hash(superuser_password)


@dataclasses.dataclass
class UserModel:
    email: str
    hashed_password: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    is_active: bool = True
    is_superuser: bool = False


@dataclasses.dataclass
class MatchModel:
    home_team: str
    away_team: str
    event_id: int
    start_time: datetime
    status: Status = Status.not_started
    home_goals: int | None = None
    away_goals: int | None = None
    id: int = dataclasses.field(default=random.randint(1, 999))


@dataclasses.dataclass
class EventModel:
    name: str
    deadline: datetime
    matches: list[MatchModel] = dataclasses.field(default_factory=lambda: [])
    status: Status = Status.not_started
    id: int = dataclasses.field(default=random.randint(1, 999))


@pytest.fixture(scope='session')
def match1() -> MatchModel:
    return MatchModel(
        id=123,
        event_id=123,
        home_team='Stoke City',
        away_team='Swansea',
        status=Status.not_started,
        start_time=datetime.utcnow(),
    )


@pytest.fixture(scope='session')
def event1(match1: MatchModel) -> EventModel:
    return EventModel(
        id=123,
        name='event1',
        status=Status.not_started,
        deadline=datetime.utcnow(),
        matches=[match1],
    )


@pytest.fixture(scope='session')
def active_user() -> UserModel:
    return UserModel(
        email="testuser@example.com",
        hashed_password=user_password_hash,
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture(scope='session')
def superuser() -> UserModel:
    return UserModel(
        email="testsuperuser@example.com",
        hashed_password=superuser_password_hash,
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture(scope='session')
def fake_get_auth_service(active_user: UserModel, superuser: UserModel):
    def _fake_get_auth_service() -> BaseAuthService:
        class MockAuthService(BaseAuthService):
            users = [active_user, superuser]

            async def get_multiple(self) -> list[UserModel]:
                return self.users

            async def get_by_id(self, user_id: UUID4) -> UserModel | None:
                for user in self.users:
                    if user.id == user_id:
                        return user
                return None

            async def get_by_email(self, email: str) -> UserModel | None:
                for user in self.users:
                    if user.email == email:
                        return user
                return None

            async def create(self, new_user: UserCreate) -> UserModel:
                hashed_password = get_password_hash(new_user.password)
                user = UserModel(
                    **new_user.dict(exclude={'password'}, exclude_none=True),
                    hashed_password=hashed_password,
                    is_active=True,
                    is_superuser=False,
                )
                return user

            async def authenticate(self, email: str, password: str) -> UserModel | None:
                for user in self.users:
                    if user.email == email and verify_password(password, user.hashed_password):
                        return user
                return None

        yield MockAuthService()

    return _fake_get_auth_service


@pytest.fixture(scope='session')
def fake_get_event_service(event1: EventModel):
    def _fake_get_event_service() -> BaseEventService:
        class MockEventService(BaseEventService):
            events = [event1]

            async def get_multiple(self, offset: int = 0, limit: int = 100) -> list[EventModel]:
                if offset > 0 or limit < 1:
                    return []
                return self.events

            async def get_by_id(self, event_id: int) -> EventModel | None:
                for event in self.events:
                    if event.id == event_id:
                        return event
                return None

            async def create(self, event: EventCreate) -> EventModel:
                new_event = EventModel(**event.dict())
                matches = [MatchModel(**match.dict(), event_id=new_event.id) for match in event.matches]
                new_event.matches = matches
                return new_event

            async def delete(self, event_id: int) -> None:
                return None

        yield MockEventService()

    return _fake_get_event_service


reusable_oauth2 = OAuth2(
    flows={
        "password": {
            "tokenUrl": "/auth/login",
            "scopes": {"read:users": "Read the users", "write:users": "Create users"},
        }
    }
)


@pytest.fixture
def fake_get_current_user(active_user: UserModel, superuser: UserModel):
    async def _fake_get_current_user(oauth_header: str = Security(reusable_oauth2)) -> UserModel | None:
        users = [active_user, superuser]
        for user in users:
            if user.email == oauth_header:
                return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return _fake_get_current_user


@pytest.fixture
def get_test_client():
    async def _get_test_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
        async with LifespanManager(app):
            async with httpx.AsyncClient(
                    app=app, base_url="http://app.io"
            ) as test_client:
                yield test_client

    return _get_test_client
