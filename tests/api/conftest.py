from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import OAuth2
from starlette import status

from src.auth.base import BaseAuthService
from src.auth.schemas import UserCreate
from src.core.security import get_password_hash, verify_password
from src.events.base import BaseEventService
from src.events.models import Status
from src.events.schemas import EventCreate
from src.matches.base import BaseMatchService
from src.matches.schemas import MatchCreate
from src.predictions.base import BasePredictionService
from src.predictions.schemas import PredictionCreate, PredictionUpdate
from tests.utils import gen_matches, MatchModel, EventModel, UserModel, PredictionModel

user_password = 'user'
superuser_password = 'admin'
user_password_hash = get_password_hash(user_password)
superuser_password_hash = get_password_hash(superuser_password)


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
        matches=[match1] + gen_matches(event_id=123, count=4),
    )


@pytest.fixture(scope='session')
def active_event(match1: MatchModel) -> EventModel:
    return EventModel(
        id=124,
        name='event1',
        status=Status.in_process,
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
def prediction1(active_user: UserModel, match1: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=active_user.id,
        match_id=match1.id,
    )


@pytest.fixture(scope='session')
def prediction2(superuser: UserModel, match1: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=superuser.id,
        match_id=match1.id,
    )


@pytest.fixture(scope='session')
def fake_get_auth_service(active_user: UserModel, superuser: UserModel):
    def _fake_get_auth_service() -> BaseAuthService:
        class MockAuthService(BaseAuthService):
            users = {
                active_user.id: active_user,
                superuser.id: superuser,
            }

            async def get_multiple(self) -> list[UserModel]:
                return list(self.users.values())

            async def get_by_id(self, user_id: UUID) -> UserModel | None:
                user = self.users.get(user_id)
                if not user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
                return user

            async def get_by_email(self, email: str) -> UserModel | None:
                for user in self.users.values():
                    if user.email == email:
                        return user
                return None

            async def register(self, new_user: UserCreate) -> UserModel:
                user = await self.get_by_email(email=new_user.email)

                if user:
                    raise HTTPException(
                        status_code=400,
                        detail="The user with this email already exists in the system.",
                    )

                hashed_password = get_password_hash(new_user.password)
                user = UserModel(
                    **new_user.dict(exclude={'password'}, exclude_none=True),
                    hashed_password=hashed_password,
                    is_active=True,
                    is_superuser=False,
                )
                return user

            async def login(self, email: str, password: str) -> UserModel | None:
                for user in self.users.values():
                    if user.email == email and verify_password(password, user.hashed_password):
                        return user
                raise HTTPException(status_code=400, detail="Incorrect email or password")

        yield MockAuthService()

    return _fake_get_auth_service


@pytest.fixture(scope='session')
def fake_get_event_service(event1: EventModel, active_event: EventModel):
    def _fake_get_event_service() -> BaseEventService:
        class MockEventService(BaseEventService):
            events = {
                event1.id: event1,
                active_event.id: active_event,
            }

            matches = {match.id: match for event in events.values() for match in event.matches}

            async def get_multiple(
                    self,
                    admin_mode: bool = False,
                    offset: int = 0,
                    limit: int = 100
            ) -> list[EventModel]:
                return list(self.events.values())

            async def get_by_id(self, event_id: int) -> EventModel | None:
                event = self.events.get(event_id)
                if not event:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='event not found')
                return event

            async def create(self, event: EventCreate) -> EventModel:
                return EventModel(**event.dict())

            async def run(self, event_id: int) -> EventModel:
                event = await self.get_by_id(event_id=event_id)

                if event.status != Status.not_started:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='You can run only not started events'
                    )

                elif len(event.matches) != 5:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Required min 5 matches')

                else:
                    return EventModel(
                        id=event.id,
                        name=event.name,
                        status=Status.in_process,
                        deadline=event.deadline,
                        matches=event.matches,
                    )

            async def delete(self, event_id: int) -> None:
                await self.get_by_id(event_id=event_id)

        yield MockEventService()

    return _fake_get_event_service


@pytest.fixture(scope='session')
def fake_get_match_service(match1: MatchModel):
    def _fake_get_match_service() -> BaseMatchService:
        class MockMatchService(BaseMatchService):
            matches = {
                match1.id: match1,
            }

            async def create(self, match: MatchCreate, event_id: int) -> MatchModel:
                return MatchModel(**match.dict(), event_id=event_id)

            async def delete(self, match_id: int) -> None:
                match = self.matches.get(match_id)

                if not match:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Match not found')

        yield MockMatchService()

    return _fake_get_match_service


@pytest.fixture(scope='session')
def fake_get_prediction_service(prediction1: PredictionModel, prediction2: PredictionModel, event1: EventModel):
    def _fake_get_prediction_service() -> BasePredictionService:
        class MockPredictionService(BasePredictionService):
            predictions = {
                prediction1.id: prediction1,
                prediction2.id: prediction2,
            }

            async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionModel]:
                event_matches = [match.id for match in event1.matches]
                return [prediction for prediction in self.predictions.values() if
                        prediction.user_id == user_id and prediction.match_id in event_matches]

            async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
                prediction = self.predictions.get(prediction_id)

                if not prediction:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Prediction not found')
                return prediction

            async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionModel:
                for predict in self.predictions.values():
                    if predict.match_id == prediction.match_id and predict.user_id == user_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Prediction for this match already exists',
                        )
                return PredictionModel(**prediction.dict(), user_id=user_id)

            async def update(self, prediction_id: int, prediction: PredictionUpdate, user_id: UUID) -> PredictionModel:
                prediction_to_update = await self.get_by_id(prediction_id=prediction_id)
                if prediction_to_update.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail='You can only edit your own predictions')
                return PredictionModel(
                    id=prediction_id,
                    home_goals=prediction.home_goals,
                    away_goals=prediction.away_goals,
                    match_id=prediction_to_update.match_id,
                    user_id=prediction_to_update.user_id,
                )

        yield MockPredictionService()

    return _fake_get_prediction_service


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
