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
from src.matches.schemas import MatchCreate, MatchUpdate, MatchRead
from src.predictions.base import BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate
from tests.utils import EventModel, gen_matches, UserModel, user_password, superuser_password, MatchModel, \
    PredictionModel


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
def created_event() -> EventModel:
    return EventModel(
        id=123,
        name='event1',
        status=EventStatus.created,
        deadline=datetime.utcnow(),
        matches=[],
    )


@pytest.fixture
def upcoming_event() -> EventModel:
    return EventModel(
        id=124,
        name='event2',
        status=EventStatus.upcoming,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=124, count=5),
    )


@pytest.fixture
def ongoing_event() -> EventModel:
    return EventModel(
        id=125,
        name='event3',
        status=EventStatus.ongoing,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=125, count=5),
    )


@pytest.fixture
def ready_to_finish_event() -> EventModel:
    return EventModel(
        id=126,
        name='event4',
        status=EventStatus.ongoing,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=126, count=5, finished=True),
    )


@pytest.fixture
def upcoming_match() -> MatchModel:
    return MatchModel(
        home_team='Chelsea',
        away_team='Man City',
        start_time=datetime.utcnow(),
        status=MatchStatus.upcoming,
        event_id=123,
    )


@pytest.fixture
def ongoing_match() -> MatchModel:
    return MatchModel(
        home_team='Real Madrid',
        away_team='Barcelona',
        start_time=datetime.utcnow(),
        status=MatchStatus.ongoing,
        event_id=123,
    )


@pytest.fixture
def completed_match() -> MatchModel:
    return MatchModel(
        home_team='Everton',
        away_team='Liverpool',
        start_time=datetime.utcnow(),
        status=MatchStatus.completed,
        event_id=123,
    )


@pytest.fixture
def prediction1(active_user: UserModel, upcoming_match: MatchModel) -> PredictionModel:
    return PredictionModel(
        home_goals=1,
        away_goals=0,
        user_id=active_user.id,
        match_id=upcoming_match.id,
    )


@pytest.fixture
def mock_auth_repo(
        active_user: UserModel,
        superuser: UserModel,
) -> BaseAuthRepository:
    class MockAuthRepository(BaseAuthRepository):
        async def get_multiple(self) -> Sequence[UserModel]:
            return [active_user, superuser]

        async def get_by_id(self, user_id: UUID) -> UserModel | None:
            if user_id == active_user.id:
                return active_user
            if user_id == superuser.id:
                return superuser
            return None

        async def get_by_email(self, email: str) -> UserModel | None:
            if email == active_user.email:
                return active_user
            if email == superuser.email:
                return superuser
            return None

        async def create(self, new_user: UserCreate) -> UserModel:
            hashed_password = get_password_hash(new_user.password)
            return UserModel(
                **new_user.dict(exclude={'password'}, exclude_none=True),
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
            )

    yield MockAuthRepository()


@pytest.fixture
def mock_event_repo(
        created_event: EventModel,
        upcoming_event: EventModel,
        ongoing_event: EventModel,
        ready_to_finish_event: EventModel,
) -> BaseEventRepository:
    class MockEventRepository(BaseEventRepository):
        async def get_multiple(
                self,
                admin_mode: bool = False,
                offset: int = 0, limit: int = 100
        ) -> Sequence[EventModel]:
            if admin_mode is True:
                return [created_event, upcoming_event, ongoing_event, ready_to_finish_event]
            else:
                return [upcoming_event, ongoing_event, ready_to_finish_event]

        async def get_by_id(self, event_id: int) -> EventModel | None:
            if event_id == created_event.id:
                return created_event
            if event_id == upcoming_event.id:
                return upcoming_event
            if event_id == ongoing_event.id:
                return ongoing_event
            if event_id == ready_to_finish_event.id:
                return ready_to_finish_event
            return None

        async def create(self, event: EventCreate) -> EventModel:
            return EventModel(**event.dict())

        async def update(self, event_id: int, event: EventUpdate) -> EventModel | None:
            if event_id == created_event.id:
                created_event.name = event.name
                created_event.status = event.status
                created_event.deadline = event.deadline
                return created_event
            if event_id == upcoming_event.id:
                upcoming_event.name = event.name
                upcoming_event.status = event.status
                upcoming_event.deadline = event.deadline
                return upcoming_event
            if event_id == ready_to_finish_event.id:
                ready_to_finish_event.name = event.name
                ready_to_finish_event.status = event.status
                ready_to_finish_event.deadline = event.deadline
                return ready_to_finish_event
            return None

        async def delete(self, event_id: int) -> None:
            return None

    yield MockEventRepository()


@pytest.fixture
def mock_match_repo(
        upcoming_match: MatchModel,
        ongoing_match: MatchModel,
        completed_match: MatchModel,
) -> BaseMatchRepository:
    class MockMatchRepository(BaseMatchRepository):
        async def create(self, match: MatchCreate, event_id: int) -> MatchModel:
            return MatchModel(**match.dict(), event_id=event_id)

        async def get_by_id(self, match_id: int) -> MatchModel | None:
            if match_id == upcoming_match.id:
                return upcoming_match
            if match_id == ongoing_match.id:
                return ongoing_match
            if match_id == completed_match.id:
                return completed_match
            return None

        async def update(self, match_id: int, match: MatchUpdate) -> MatchModel:
            if match_id == ongoing_match.id:
                ongoing_match.home_team = match.home_team
                ongoing_match.away_team = match.away_team
                ongoing_match.start_time = match.start_time
                ongoing_match.status = match.status
                ongoing_match.home_goals = match.home_goals
                ongoing_match.away_goals = match.away_goals
                return ongoing_match

        async def delete(self, match_id: int) -> None:
            return None

    yield MockMatchRepository()


@pytest.fixture
def mock_prediction_repo(prediction1: PredictionModel) -> BasePredictionRepository:
    class MockPredictionRepository(BasePredictionRepository):
        async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionModel]:
            return [prediction1]

        async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
            if prediction_id == prediction1.id:
                return prediction1
            return None

        async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionModel:
            return PredictionModel(**prediction.dict(), user_id=user_id)

        async def update(self, prediction_id: int, prediction: PredictionUpdate) -> PredictionModel | None:
            if prediction_id == prediction1.id:
                return PredictionModel(
                    id=prediction1.id,
                    home_goals=prediction.home_goals,
                    away_goals=prediction.away_goals,
                    user_id=prediction1.user_id,
                    match_id=prediction1.match_id,
                )

        async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
            if user_id == prediction1.user_id and match_id == prediction1.match_id:
                return True
            return False

        async def update_points_for_match(self, match: MatchRead) -> None:
            pass

    yield MockPredictionRepository()
