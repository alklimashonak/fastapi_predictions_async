import logging
from datetime import datetime
from typing import Sequence
from uuid import UUID

import pytest

from src.auth.base import BaseAuthRepository
from src.auth.schemas import UserCreate
from src.core.security import get_password_hash
from src.events.base import BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import EventCreate, EventUpdate
from src.matches.base import BaseMatchRepository
from src.matches.models import MatchStatus
from src.matches.schemas import MatchCreate
from src.predictions.base import BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate
from tests.utils import MatchModel, EventModel, UserModel, PredictionModel, user_password, superuser_password

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def active_user() -> UserModel:
    return UserModel(
        email="testuser@example.com",
        hashed_password=get_password_hash(user_password),
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture(scope='session')
def superuser() -> UserModel:
    return UserModel(
        email="testsuperuser@example.com",
        hashed_password=get_password_hash(superuser_password),
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture
def match1() -> MatchModel:
    return MatchModel(
        id=123,
        event_id=123,
        home_team='Stoke City',
        away_team='Swansea',
        status=MatchStatus.upcoming,
        start_time=datetime.utcnow(),
    )


@pytest.fixture
def event1(match1: MatchModel) -> EventModel:
    return EventModel(
        id=123,
        name='event1',
        status=EventStatus.created,
        deadline=datetime.utcnow(),
        matches=[match1],
    )


@pytest.fixture
def event2() -> EventModel:
    return EventModel(
        id=124,
        name='event2',
        status=EventStatus.upcoming,
        deadline=datetime.utcnow(),
        matches=[],
    )


@pytest.fixture
def prediction1(active_user: UserModel, match1: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=active_user.id,
        match_id=match1.id,
    )


@pytest.fixture
def prediction2(superuser: UserModel, match1: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=superuser.id,
        match_id=match1.id,
    )


@pytest.fixture(scope='session')
def mock_auth_repo():
    class MockAuthRepository(BaseAuthRepository):
        def __init__(self, users: list[UserModel]):
            self.users = users

        async def get_multiple(self) -> Sequence[UserModel]:
            return self.users

        async def get_by_id(self, user_id: UUID) -> UserModel | None:
            for user in self.users:
                if user.id == user_id:
                    return user

        async def get_by_email(self, email: str) -> UserModel | None:
            for user in self.users:
                if user.email == email:
                    return user

        async def create(self, new_user: UserCreate) -> UserModel:
            hashed_password = get_password_hash(new_user.password)
            user = UserModel(
                **new_user.dict(exclude={'password'}, exclude_none=True),
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
            )
            return user

    yield MockAuthRepository


@pytest.fixture(scope='session')
def mock_event_repo():
    class MockEventRepository(BaseEventRepository):
        def __init__(self, events: list[EventModel]):
            self.events = events

        async def get_multiple(
                self,
                admin_mode: bool = False,
                offset: int = 0, limit: int = 100
        ) -> Sequence[EventModel]:
            if offset > 0 or limit < 1:
                return []
            return self.events

        async def get_by_id(self, event_id: int) -> EventModel | None:
            for event in self.events:
                if event.id == event_id:
                    return event

        async def create(self, event: EventCreate) -> EventModel:
            return EventModel(**event.dict())

        async def update(self, event_id: int, event: EventUpdate) -> EventModel | None:
            for ev in self.events:
                if ev.id == event_id:
                    ev.name = event.name
                    ev.deadline = event.deadline
                    ev.status = event.status
                    return ev

        async def delete(self, event_id: int) -> None:
            return

    yield MockEventRepository


@pytest.fixture(scope='session')
def mock_match_repo():
    class MockMatchRepository(BaseMatchRepository):
        def __init__(self, matches):
            self.matches = matches

        async def create(self, match: MatchCreate, event_id: int) -> MatchModel:
            return MatchModel(**match.dict(), event_id=event_id)

        async def get_by_id(self, match_id: int) -> MatchModel | None:
            for match in self.matches:
                if match.id == match_id:
                    return match

        async def delete(self, match_id: int) -> None:
            return

    yield MockMatchRepository


@pytest.fixture(scope='session')
def mock_prediction_repo():
    class MockPredictionRepository(BasePredictionRepository):
        def __init__(self, users: list[UserModel], events: list[EventModel], predictions: list[PredictionModel]):
            self.users = users
            self.events = events
            self.predictions = predictions

        async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionModel]:
            if user_id not in [user.id for user in self.users]:
                return []
            try:
                event = [event for event in self.events if event.id == event_id][0]
            except IndexError:
                return []

            event_matches_ids = [match.id for match in event.matches]
            return [prediction for prediction in self.predictions if
                    prediction.user_id == user_id and prediction.match_id in event_matches_ids]

        async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
            for prediction in self.predictions:
                if prediction.id == prediction_id:
                    return prediction

        async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionModel:
            return PredictionModel(**prediction.dict(), user_id=user_id)

        async def update(self, prediction_id: int, prediction: PredictionUpdate) -> PredictionModel | None:
            prediction_to_update = await self.get_by_id(prediction_id=prediction_id)

            if not prediction_to_update:
                return

            return PredictionModel(
                id=prediction_id,
                home_goals=prediction.home_goals,
                away_goals=prediction.away_goals,
                match_id=prediction_to_update.match_id,
                user_id=prediction_to_update.user_id,
            )

        async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
            for prediction in self.predictions:
                if prediction.user_id == user_id and prediction.match_id == match_id:
                    return True
            return False

    yield MockPredictionRepository
