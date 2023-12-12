from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import httpx
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import OAuth2
from pydantic import EmailStr
from starlette import status

from src import exceptions
from src.auth.base import BaseAuthService
from src.auth.schemas import UserCreate, UserRead
from src.core.config import settings
from src.core.security import get_password_hash, verify_password
from src.events.base import BaseEventService
from src.events.models import EventStatus
from src.events.schemas import EventCreate, EventRead
from src.matches.base import BaseMatchService
from src.matches.models import MatchStatus
from src.matches.schemas import MatchCreate, MatchRead
from src.predictions.base import BasePredictionService
from src.predictions.schemas import PredictionCreate, PredictionUpdate, PredictionRead
from tests.utils import gen_matches, MatchModel, EventModel, UserModel, PredictionModel


@pytest.fixture(scope='session')
def upcoming_match() -> MatchModel:
    return MatchModel(
        id=123,
        event_id=123,
        home_team='Stoke City',
        away_team='Swansea',
        status=MatchStatus.upcoming,
        start_time=datetime.utcnow(),
    )


@pytest.fixture(scope='session')
def upcoming_match2() -> MatchModel:
    return MatchModel(
        id=124,
        event_id=123,
        home_team='Stoke City',
        away_team='Swansea',
        status=MatchStatus.upcoming,
        start_time=datetime.utcnow(),
    )


@pytest.fixture(scope='session')
def ongoing_match() -> MatchModel:
    return MatchModel(
        id=125,
        event_id=123,
        home_team='Stoke City',
        away_team='Swansea',
        status=MatchStatus.ongoing,
        start_time=datetime.utcnow(),
    )


@pytest.fixture(scope='session')
def completed_match() -> MatchModel:
    return MatchModel(
        id=126,
        event_id=123,
        home_team='Everton',
        away_team='Hull City',
        status=MatchStatus.completed,
        start_time=datetime.utcnow(),
    )


@pytest.fixture(scope='session')
def created_event() -> EventModel:
    return EventModel(
        id=123,
        name='event1',
        status=EventStatus.created,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=123),
    )


@pytest.fixture(scope='session')
def upcoming_event() -> EventModel:
    return EventModel(
        id=124,
        name='event2',
        status=EventStatus.upcoming,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=124),
    )


@pytest.fixture(scope='session')
def ongoing_event() -> EventModel:
    return EventModel(
        id=125,
        name='event3',
        status=EventStatus.ongoing,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=125),
    )


@pytest.fixture(scope='session')
def ready_to_finish_event() -> EventModel:
    return EventModel(
        id=126,
        name='event4',
        status=EventStatus.closed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=126, finished=True),
    )


@pytest.fixture(scope='session')
def closed_event() -> EventModel:
    return EventModel(
        id=128,
        name='event6',
        status=EventStatus.closed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=128),
    )


@pytest.fixture(scope='session')
def event_without_matches() -> EventModel:
    return EventModel(
        id=127,
        name='event5',
        status=EventStatus.created,
        deadline=datetime.utcnow(),
        matches=[],
    )


@pytest.fixture(scope='session')
def completed_event() -> EventModel:
    return EventModel(
        id=129,
        name='event7',
        status=EventStatus.completed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=129, finished=True),
    )


@pytest.fixture(scope='session')
def active_user() -> UserModel:
    return UserModel(
        email=settings.TEST_USER_EMAIL,
        hashed_password=get_password_hash(settings.TEST_USER_PASSWORD),
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture(scope='session')
def superuser() -> UserModel:
    return UserModel(
        email=settings.TEST_SUPERUSER_EMAIL,
        hashed_password=get_password_hash(settings.TEST_SUPERUSER_PASSWORD),
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture(scope='session')
def prediction1(active_user: UserModel, upcoming_match: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=2,
        away_goals=0,
        user_id=active_user.id,
        match_id=upcoming_match.id,
    )


@pytest.fixture(scope='session')
def prediction2(superuser: UserModel, upcoming_match: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=superuser.id,
        match_id=upcoming_match.id,
    )


@pytest.fixture(scope='session')
def fake_get_auth_service(active_user: UserModel, superuser: UserModel):
    def _fake_get_auth_service() -> BaseAuthService:
        class MockAuthService(BaseAuthService):
            users = [active_user, superuser]

            async def get_multiple(self) -> list[UserRead]:
                return [UserRead.from_orm(user) for user in self.users]

            async def get_by_id(self, user_id: UUID) -> UserRead | None:
                user = self._get_by_id(user_id=user_id)

                if user is None:
                    raise exceptions.UserNotFound

                return UserRead.from_orm(user)

            async def get_by_email(self, email: str) -> UserRead:
                pass

            async def register(self, new_user: UserCreate) -> UserRead:
                user = await self._get_by_email(email=new_user.email)

                if user is not None:
                    raise exceptions.UserAlreadyExists

                hashed_password = get_password_hash(new_user.password)
                user = UserModel(
                    **new_user.dict(exclude={'password'}, exclude_none=True),
                    hashed_password=hashed_password,
                    is_active=True,
                    is_superuser=False,
                )
                return UserRead.from_orm(user)

            async def login(self, email: str, password: str) -> UserRead:
                if email == active_user.email and verify_password(password, active_user.hashed_password):
                    return UserRead.from_orm(active_user)
                if email == superuser.email and verify_password(password, superuser.hashed_password):
                    return UserRead.from_orm(superuser)
                raise exceptions.InvalidEmailOrPassword

            async def _get_by_id(self, user_id: UUID) -> UserModel | None:
                for user in self.users:
                    if user.id == user_id:
                        return user
                else:
                    return None

            async def _get_by_email(self, email: EmailStr) -> UserModel | None:
                for user in self.users:
                    if user.email == email:
                        return user
                else:
                    return None

        yield MockAuthService()

    return _fake_get_auth_service


@pytest.fixture(scope='session')
def fake_get_event_service(
        created_event: EventModel,
        upcoming_event: EventModel,
        ongoing_event: EventModel,
        ready_to_finish_event: EventModel,
        event_without_matches: EventModel,
        closed_event: EventModel,
        completed_event: EventModel,
):
    def _fake_get_event_service() -> BaseEventService:
        class MockEventService(BaseEventService):
            events = [created_event, upcoming_event, ongoing_event, ready_to_finish_event, event_without_matches,
                      closed_event, completed_event]

            async def get_multiple(
                    self,
                    admin_mode: bool = False,
                    offset: int = 0,
                    limit: int = 100
            ) -> list[EventRead]:
                if admin_mode is True:
                    return [EventRead.from_orm(event) for event in self.events]
                else:
                    return [EventRead.from_orm(event) for event in self.events if event.status != EventStatus.created]

            async def get_by_id(self, event_id: int) -> EventRead | None:
                event = await self._get_by_id(event_id=event_id)

                if event is None:
                    raise exceptions.EventNotFound

                return EventRead.from_orm(event)

            async def create(self, event: EventCreate) -> EventRead:
                new_event = EventModel(**event.dict())
                return EventRead.from_orm(new_event)

            async def upgrade_status(self, event_id: int) -> EventRead:
                event = await self._get_by_id(event_id=event_id)

                if event is None:
                    raise exceptions.EventNotFound
                if event.status == EventStatus.completed:
                    raise exceptions.UnexpectedEventStatus
                if event.status == EventStatus.closed:
                    for match in event.matches:
                        if match.status != MatchStatus.completed:
                            raise exceptions.MatchesAreNotFinished
                if event.status == EventStatus.created:
                    if len(event.matches) != 5:
                        raise exceptions.TooFewMatches

                event_scheme = EventRead.from_orm(event)
                event_scheme.status = event.status + 1

                return event_scheme

            async def delete(self, event_id: int) -> None:
                event = await self._get_by_id(event_id=event_id)

                if event is None:
                    raise exceptions.EventNotFound
                else:
                    return None

            async def _get_by_id(self, event_id: int) -> EventModel | None:
                for event in self.events:
                    if event.id == event_id:
                        return event
                else:
                    return None

        yield MockEventService()

    return _fake_get_event_service


@pytest.fixture(scope='session')
def fake_get_match_service(
        upcoming_match: MatchModel,
        upcoming_match2: MatchModel,
        ongoing_match: MatchModel,
        completed_match: MatchModel,
        created_event: EventModel,
        upcoming_event: EventModel,
        ongoing_event: EventModel,
        ready_to_finish_event: EventModel,
        event_without_matches: EventModel,
):
    def _fake_get_match_service() -> BaseMatchService:
        class MockMatchService(BaseMatchService):
            events = [created_event, upcoming_event, ongoing_event, ready_to_finish_event, event_without_matches]
            matches = [upcoming_match, upcoming_match2, ongoing_match, completed_match]

            async def create(self, match: MatchCreate, event_id: int) -> MatchRead:
                event = await self._get_event_by_id(event_id=event_id)

                if event is None:
                    raise exceptions.EventNotFound

                if event.status != EventStatus.created:
                    raise exceptions.UnexpectedEventStatus

                if len(event.matches) == settings.MATCHES_COUNT:
                    raise exceptions.MatchesLimitError

                new_match = MatchModel(**match.dict(), event_id=event_id)
                return MatchRead.from_orm(new_match)

            async def finish(self, match_id: int, home_goals: int, away_goals: int) -> MatchRead:
                match = await self._get_match_by_id(match_id=match_id)

                if match is None:
                    raise exceptions.MatchNotFound

                if match.status == MatchStatus.completed:
                    raise exceptions.UnexpectedMatchStatus

                if match.status == MatchStatus.ongoing:
                    match_scheme = MatchRead.from_orm(match)
                    match_scheme.home_goals = home_goals
                    match_scheme.away_goals = away_goals
                    match_scheme.status = MatchStatus.completed
                    return match_scheme

                if match.status == MatchStatus.upcoming:
                    match_scheme = MatchRead.from_orm(match)
                    match_scheme.home_goals = home_goals
                    match_scheme.away_goals = away_goals
                    match_scheme.status = MatchStatus.completed
                    return match_scheme

            async def delete(self, match_id: int) -> None:
                match = await self._get_match_by_id(match_id=match_id)

                if match is None:
                    raise exceptions.MatchNotFound
                else:
                    return None

            async def _get_match_by_id(self, match_id: int) -> MatchModel | None:
                for match in self.matches:
                    if match.id == match_id:
                        return match
                else:
                    return None

            async def _get_event_by_id(self, event_id: int) -> EventModel | None:
                for event in self.events:
                    if event.id == event_id:
                        return event
                else:
                    return None

        yield MockMatchService()

    return _fake_get_match_service


@pytest.fixture(scope='session')
def fake_get_prediction_service(
        prediction1: PredictionModel,
        prediction2: PredictionModel,
        ongoing_event: EventModel,
        active_user: UserModel,
        superuser: UserModel,
        upcoming_match: MatchModel,
        upcoming_match2: MatchModel,
        ongoing_match: MatchModel,
        completed_match: MatchModel,
):
    def _fake_get_prediction_service() -> BasePredictionService:
        class MockPredictionService(BasePredictionService):
            users = [active_user, superuser]
            events = [ongoing_event]
            predictions = [prediction1, prediction2]
            matches = [upcoming_match, upcoming_match2, ongoing_match, completed_match]

            async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionRead]:
                event = await self._get_event_by_id(event_id=event_id)
                match_ids = [match.id for match in event.matches]

                predictions = [PredictionRead.from_orm(predict) for predict in self.predictions if
                               predict.user_id == user_id and predict.match_id in match_ids]

                return predictions

            async def get_by_id(self, prediction_id: int) -> PredictionRead:
                prediction = self._get_prediction_by_id(prediction_id=prediction_id)

                if prediction is None:
                    raise exceptions.PredictionNotFound

                return PredictionRead.from_orm(prediction)

            async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionRead:
                match = await self._get_match_by_id(match_id=prediction.match_id)

                if not match:
                    raise exceptions.MatchNotFound

                if match.status != MatchStatus.upcoming:
                    raise exceptions.UnexpectedMatchStatus

                for predict in self.predictions:
                    if predict.match_id == prediction.match_id and predict.user_id == user_id:
                        raise exceptions.PredictionAlreadyExists

                prediction = PredictionModel(**prediction.dict(), user_id=user_id)

                return PredictionRead.from_orm(prediction)

            async def update(self, prediction_id: int, prediction: PredictionUpdate, user_id: UUID) -> PredictionRead:
                predict = await self._get_prediction_by_id(prediction_id=prediction_id)

                if predict is None:
                    raise exceptions.PredictionNotFound

                match = await self._get_match_by_id(match_id=predict.match_id)

                if match is None:
                    raise exceptions.MatchNotFound

                if match.status != MatchStatus.upcoming:
                    raise exceptions.UnexpectedMatchStatus

                if user_id != predict.user_id:
                    raise exceptions.UserIsNotAllowed

                prediction_scheme = PredictionRead.from_orm(predict)
                prediction_scheme.home_goals = prediction.home_goals
                prediction_scheme.away_goals = prediction.away_goals
                return prediction_scheme

            async def _get_match_by_id(self, match_id: int) -> MatchModel | None:
                for match in self.matches:
                    if match.id == match_id:
                        return match
                else:
                    return None

            async def _get_prediction_by_id(self, prediction_id: int) -> PredictionModel | None:
                for prediction in self.predictions:
                    if prediction.id == prediction_id:
                        return prediction
                else:
                    return None

            async def _get_user_by_id(self, user_id: int) -> UserModel | None:
                for user in self.users:
                    if user.id == user_id:
                        return user
                else:
                    return None

            async def _get_event_by_id(self, event_id: int) -> EventModel | None:
                for event in self.events:
                    if event.id == event_id:
                        return event
                else:
                    return None

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
