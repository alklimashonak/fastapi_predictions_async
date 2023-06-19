import dataclasses
import uuid
import random
from datetime import datetime
from typing import Optional, Union, Dict, Any, Type, Generic, AsyncGenerator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi_users.password import PasswordHelper
from pydantic import UUID4
from pytest_mock import MockerFixture
from fastapi import Response, FastAPI

from fastapi_users import exceptions, models, schemas
from fastapi_users.models import UP
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy import Strategy
from fastapi_users.db import BaseUserDatabase
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users.openapi import OpenAPIResponseType

from src.events.base import BaseEventDatabase
from src.events.models import MatchProtocol, MatchStatus, EventProtocol, EventStatus
from src.events.schemas import EventCreate, EventUpdate

IDType = uuid.UUID

password_helper = PasswordHelper()
guinevere_password_hash = password_helper.hash("guinevere")
angharad_password_hash = password_helper.hash("angharad")
viviane_password_hash = password_helper.hash("viviane")
lancelot_password_hash = password_helper.hash("lancelot")
excalibur_password_hash = password_helper.hash("excalibur")


@dataclasses.dataclass
class UserModel(models.UserProtocol[IDType]):
    email: str
    hashed_password: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    first_name: Optional[str] = None


@dataclasses.dataclass
class MatchModel(MatchProtocol):
    team1: str
    team2: str
    status: MatchStatus
    start_time: datetime
    team1_goals: int | None
    team2_goals: int | None
    event_id: int
    id: int = dataclasses.field(default=random.randint(1, 999))


@dataclasses.dataclass
class EventModel(EventProtocol):
    name: str
    status: EventStatus
    start_time: datetime
    matches: list[MatchModel]
    id: int = dataclasses.field(default=random.randint(1, 999))


class User(schemas.BaseUser[IDType]):
    first_name: Optional[str]


class UserUpdate(schemas.BaseUserUpdate):
    first_name: Optional[str]


@pytest.fixture
def user() -> UserModel:
    return UserModel(
        email="king.arthur@camelot.bt",
        hashed_password=guinevere_password_hash,
    )


@pytest.fixture
def inactive_user() -> UserModel:
    return UserModel(
        email="percival@camelot.bt",
        hashed_password=angharad_password_hash,
        is_active=False,
    )


@pytest.fixture
def verified_user() -> UserModel:
    return UserModel(
        email="lake.lady@camelot.bt",
        hashed_password=excalibur_password_hash,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def superuser() -> UserModel:
    return UserModel(
        email="merlin@camelot.bt",
        hashed_password=viviane_password_hash,
        is_superuser=True,
    )


@pytest.fixture
def verified_superuser() -> UserModel:
    return UserModel(
        email="the.real.merlin@camelot.bt",
        hashed_password=viviane_password_hash,
        is_superuser=True,
        is_verified=True,
    )


class BaseTestUserManager(
    Generic[UP], UUIDIDMixin, BaseUserManager[models.UP, IDType]
):
    reset_password_token_secret = "SECRET"
    verification_token_secret = "SECRET"

    async def validate_password(
            self, password: str, user: Union[schemas.UC, models.UP]
    ) -> None:
        if len(password) < 3:
            raise exceptions.InvalidPasswordException(
                reason="Password should be at least 3 characters"
            )


class UserManager(BaseTestUserManager[UserModel]):
    pass


@pytest.fixture
def mock_user_db(
        user: UserModel,
        verified_user: UserModel,
        inactive_user: UserModel,
        superuser: UserModel,
        verified_superuser: UserModel,
) -> BaseUserDatabase[UserModel, IDType]:
    class MockUserDatabase(BaseUserDatabase[UserModel, IDType]):
        async def get(self, id: UUID4) -> Optional[UserModel]:
            if id == user.id:
                return user
            if id == verified_user.id:
                return verified_user
            if id == inactive_user.id:
                return inactive_user
            if id == superuser.id:
                return superuser
            if id == verified_superuser.id:
                return verified_superuser
            return None

        async def get_by_email(self, email: str) -> Optional[UserModel]:
            lower_email = email.lower()
            if lower_email == user.email.lower():
                return user
            if lower_email == verified_user.email.lower():
                return verified_user
            if lower_email == inactive_user.email.lower():
                return inactive_user
            if lower_email == superuser.email.lower():
                return superuser
            if lower_email == verified_superuser.email.lower():
                return verified_superuser
            return None

        async def create(self, create_dict: Dict[str, Any]) -> UserModel:
            return UserModel(**create_dict)

        async def update(
                self, user: UserModel, update_dict: Dict[str, Any]
        ) -> UserModel:
            for field, value in update_dict.items():
                setattr(user, field, value)
            return user

        async def delete(self, user: UserModel) -> None:
            pass

    return MockUserDatabase()


def mock_event_db() -> BaseEventDatabase:
    class MockEventDatabase(BaseEventDatabase):
        existing_event = EventModel(
            id=123,
            name='Existing event',
            status=EventStatus.not_started,
            start_time=datetime.utcnow(),
            matches=[
                MatchModel(
                    id=123,
                    event_id=123,
                    team1='Stoke City',
                    team2='Swansea',
                    status=MatchStatus.not_started,
                    start_time=datetime.utcnow(),
                    team1_goals=None,
                    team2_goals=None,
                )
            ],
        )

        async def get_events(self) -> list[EventModel]:
            return [self.existing_event]

        async def get_event_by_id(self, event_id: int) -> EventModel | None:
            if event_id == self.existing_event.id:
                return self.existing_event
            return None

        async def create_event(self, event: EventCreate) -> EventModel:
            new_event = EventModel(**event.dict())
            matches = [MatchModel(**match.dict(), event_id=new_event.id) for match in event.matches]
            new_event.matches = matches
            return new_event

        async def update_event(
                self, event_id: int, event: EventUpdate
        ) -> EventModel | None:
            if event_id == self.existing_event.id:
                updated_event = EventModel(
                    **event.dict(exclude={'new_matches', 'matches_to_update', 'matches_to_delete'}),
                    matches=[],
                    id=self.existing_event.id
                )
                matches = self.existing_event.matches

                if event.new_matches:
                    new_matches = [MatchModel(**match.dict(), event_id=updated_event.id) for match in event.new_matches]
                    matches.extend(new_matches)

                if event.matches_to_update:
                    updated_matches_ids = [match.id for match in event.matches_to_update]
                    matches = [match for match in matches if match.id not in updated_matches_ids]

                    updated_matches = [MatchModel(**match.dict(), event_id=updated_event.id) for match in
                                       event.matches_to_update]

                    matches.extend(updated_matches)

                if event.matches_to_delete:
                    matches = [match for match in matches if match.id not in event.matches_to_delete]

                updated_event.matches = matches

                return updated_event
            return None

        async def delete_event(self, event_id: int) -> None:
            return None

    return MockEventDatabase()


async def override_get_event_db():
    yield mock_event_db()


@pytest.fixture
def make_user_manager(mocker: MockerFixture):
    def _make_user_manager(user_manager_class: Type[BaseTestUserManager], mock_user_db):
        user_manager = user_manager_class(mock_user_db)
        mocker.spy(user_manager, "get_by_email")
        mocker.spy(user_manager, "request_verify")
        mocker.spy(user_manager, "verify")
        mocker.spy(user_manager, "forgot_password")
        mocker.spy(user_manager, "reset_password")
        mocker.spy(user_manager, "on_after_register")
        mocker.spy(user_manager, "on_after_request_verify")
        mocker.spy(user_manager, "on_after_verify")
        mocker.spy(user_manager, "on_after_forgot_password")
        mocker.spy(user_manager, "on_after_reset_password")
        mocker.spy(user_manager, "on_after_update")
        mocker.spy(user_manager, "on_before_delete")
        mocker.spy(user_manager, "on_after_delete")
        mocker.spy(user_manager, "on_after_login")
        mocker.spy(user_manager, "_update")
        return user_manager

    return _make_user_manager


@pytest.fixture
def user_manager(make_user_manager, mock_user_db):
    return make_user_manager(UserManager, mock_user_db)


@pytest.fixture
def get_user_manager(user_manager):
    def _get_user_manager():
        return user_manager

    return _get_user_manager


class MockTransport(BearerTransport):
    def __init__(self, tokenUrl: str):
        super().__init__(tokenUrl)

    async def get_logout_response(self) -> Any:
        return Response()

    @staticmethod
    def get_openapi_logout_responses_success() -> OpenAPIResponseType:
        return {}


class MockStrategy(Strategy[UserModel, IDType]):
    async def read_token(
            self, token: str | None, user_manager: BaseUserManager[UserModel, IDType]
    ) -> UserModel | None:
        if token is not None:
            try:
                parsed_id = user_manager.parse_id(token)
                return await user_manager.get(parsed_id)
            except (exceptions.InvalidID, exceptions.UserNotExists):
                return None
        return None

    async def write_token(self, user: UserModel) -> str:
        return str(user.id)

    async def destroy_token(self, token: str, user: UserModel) -> None:
        return None


def get_mock_authentication(name: str):
    return AuthenticationBackend(
        name=name,
        transport=MockTransport(tokenUrl="/login"),
        get_strategy=lambda: MockStrategy(),
    )


@pytest.fixture
def mock_authentication():
    return get_mock_authentication(name="mock")


@pytest.fixture
def get_test_client():
    async def _get_test_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
        async with LifespanManager(app):
            async with httpx.AsyncClient(
                    app=app, base_url="http://app.io"
            ) as test_client:
                yield test_client

    return _get_test_client
