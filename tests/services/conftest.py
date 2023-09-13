import dataclasses
import logging
from datetime import datetime
from itertools import count
from typing import Sequence
from uuid import UUID, uuid4

import pytest

from src.auth.base import BaseAuthRepository
from src.auth.schemas import UserCreate
from src.core.security import get_password_hash
from src.events.base import BaseEventRepository
from src.events.models import Status
from src.events.schemas import EventCreate, MatchCreate
from src.predictions.base import BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate

logger = logging.getLogger(__name__)

user_password = 'user'
superuser_password = 'admin'
user_password_hash = get_password_hash(user_password)
superuser_password_hash = get_password_hash(superuser_password)


@dataclasses.dataclass
class UserModel:
    email: str
    hashed_password: str
    id: UUID = dataclasses.field(default_factory=uuid4)
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
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class EventModel:
    name: str
    deadline: datetime
    matches: list[MatchModel] = dataclasses.field(default_factory=lambda: [])
    status: Status = Status.not_started
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class PredictionModel:
    home_goals: int
    away_goals: int
    match_id: int
    user_id: UUID
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


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
def mock_auth_repo(active_user: UserModel, superuser: UserModel):
    class MockAuthRepository(BaseAuthRepository):
        users = [active_user, superuser]

        async def get_multiple(self) -> Sequence[UserModel]:
            return self.users

        async def get_by_id(self, user_id: UUID) -> UserModel | None:
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

    yield MockAuthRepository()


@pytest.fixture(scope='session')
def mock_event_repo(event1: EventModel, match1: MatchModel):
    class MockEventRepository(BaseEventRepository):
        events = [event1]
        matches = [match1]

        async def get_multiple(
                self,
                admin_mode: bool = False,
                offset: int = 0, limit: int = 100
        ) -> Sequence[EventModel]:
            if offset > 0 or limit < 1:
                return []
            return self.events

        async def get_by_id(self, event_id: int) -> EventModel | None:
            if event_id == event1.id:
                return event1
            return

        async def create(self, event: EventCreate) -> EventModel:
            new_event = EventModel(**event.dict())
            matches = [MatchModel(**match.dict(), event_id=new_event.id) for match in event.matches]
            new_event.matches = matches
            return new_event

        async def run(self, event_id: int) -> EventModel | None:
            if event_id == event1.id:
                event1.status = Status.in_process
                return event1
            return

        async def delete(self, event_id: int) -> None:
            return

        async def create_match(self, match: MatchCreate, event_id: int) -> MatchModel:
            return MatchModel(**match.dict(), event_id=event_id)

        async def _get_match_by_id(self, match_id: int) -> MatchModel | None:
            if match_id == match1.id:
                return match1
            return

        async def _create_matches(self, matches: list[MatchCreate], event_id: int) -> None:
            pass

        async def delete_match_by_id(self, match_id: int) -> None:
            return

    yield MockEventRepository()


@pytest.fixture(scope='session')
def mock_prediction_repo(prediction1: PredictionModel, prediction2: PredictionModel, event1: EventModel):
    class MockPredictionRepository(BasePredictionRepository):
        predictions = [prediction1, prediction2]

        async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionModel]:
            event_matches = [match.id for match in event1.matches]
            return [prediction for prediction in self.predictions if
                    prediction.user_id == user_id and prediction.match_id in event_matches]

        async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
            for prediction in self.predictions:
                if prediction.id == prediction_id:
                    return prediction
            return

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

    yield MockPredictionRepository()
