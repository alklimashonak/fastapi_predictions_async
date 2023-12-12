from datetime import datetime
from typing import Sequence
from uuid import UUID

import pytest

from src.auth.base import BaseAuthRepository
from src.auth.schemas import UserCreate
from src.core.config import settings
from src.core.security import get_password_hash
from src.events.base import BaseEventRepository
from src.events.models import EventStatus
from src.events.schemas import EventCreate, EventUpdate
from src.matches.base import BaseMatchRepository
from src.matches.models import MatchStatus
from src.matches.schemas import MatchCreate, MatchUpdate, MatchRead
from src.predictions.base import BasePredictionRepository
from src.predictions.schemas import PredictionCreate, PredictionUpdate
from tests.utils import EventModel, gen_matches, UserModel, MatchModel, PredictionModel


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


@pytest.fixture
def created_event() -> EventModel:
    return EventModel(
        id=1,
        name='event1',
        status=EventStatus.created,
        deadline=datetime.utcnow(),
        matches=[],
    )


@pytest.fixture
def upcoming_event() -> EventModel:
    return EventModel(
        id=2,
        name='event2',
        status=EventStatus.upcoming,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=2),
    )


@pytest.fixture
def ongoing_event() -> EventModel:
    return EventModel(
        id=3,
        name='event3',
        status=EventStatus.ongoing,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=3),
    )


@pytest.fixture
def closed_event() -> EventModel:
    return EventModel(
        id=4,
        name='event4',
        status=EventStatus.closed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=4),
    )


@pytest.fixture
def ready_to_finish_event() -> EventModel:
    return EventModel(
        id=5,
        name='event5',
        status=EventStatus.closed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=5, finished=True),
    )


@pytest.fixture
def completed_event() -> EventModel:
    return EventModel(
        id=6,
        name='event6',
        status=EventStatus.completed,
        deadline=datetime.utcnow(),
        matches=gen_matches(event_id=6, finished=True),
    )


@pytest.fixture
def upcoming_match() -> MatchModel:
    return MatchModel(
        home_team='Chelsea',
        away_team='Man City',
        start_time=datetime.utcnow(),
        status=MatchStatus.upcoming,
        event_id=2,
    )


@pytest.fixture
def ongoing_match() -> MatchModel:
    return MatchModel(
        home_team='Real Madrid',
        away_team='Barcelona',
        start_time=datetime.utcnow(),
        status=MatchStatus.ongoing,
        event_id=4,
    )


@pytest.fixture
def completed_match() -> MatchModel:
    return MatchModel(
        home_team='Everton',
        away_team='Liverpool',
        start_time=datetime.utcnow(),
        status=MatchStatus.completed,
        event_id=4,
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
        closed_event: EventModel,
        ready_to_finish_event: EventModel,
        completed_event: EventModel,
) -> BaseEventRepository:
    class MockEventRepository(BaseEventRepository):
        events = [created_event, upcoming_event, ongoing_event, closed_event, ready_to_finish_event, completed_event]

        async def get_multiple(
                self,
                admin_mode: bool = False,
                offset: int = 0, limit: int = 100
        ) -> Sequence[EventModel]:
            if admin_mode is True:
                return self.events
            else:
                return [event for event in self.events if event.status != EventStatus.created]

        async def get_by_id(self, event_id: int) -> EventModel | None:
            return await self._get_by_id(event_id=event_id)

        async def create(self, event: EventCreate) -> EventModel:
            return EventModel(**event.dict())

        async def update(self, event_id: int, event_data: EventUpdate) -> EventModel | None:
            event = await self._get_by_id(event_id=event_id)

            if event is None:
                return None

            event.name = event_data.name
            event.status = event_data.status
            event.deadline = event_data.status

            return event

        async def delete(self, event_id: int) -> None:
            return None

        async def _get_by_id(self, event_id: int) -> EventModel | None:
            for event in self.events:
                if event.id == event_id:
                    return event
            else:
                return None

    yield MockEventRepository()


@pytest.fixture
def mock_match_repo(
        upcoming_match: MatchModel,
        ongoing_match: MatchModel,
        completed_match: MatchModel,
) -> BaseMatchRepository:
    class MockMatchRepository(BaseMatchRepository):
        matches = [upcoming_match, ongoing_match, completed_match]

        async def create(self, match: MatchCreate, event_id: int) -> MatchModel:
            return MatchModel(**match.dict(), event_id=event_id)

        async def get_by_id(self, match_id: int) -> MatchModel | None:
            return await self._get_by_id(match_id=match_id)

        async def update(self, match_id: int, match_data: MatchUpdate) -> MatchModel | None:
            match = await self._get_by_id(match_id=match_id)

            if match is None:
                return None

            match.home_team = match_data.home_team
            match.away_team = match_data.away_team
            match.start_time = match_data.start_time
            match.status = match_data.status
            match.home_goals = match_data.home_goals
            match.away_goals = match_data.away_goals

            return match

        async def delete(self, match_id: int) -> None:
            return None

        async def _get_by_id(self, match_id: int) -> MatchModel | None:
            for match in self.matches:
                if match.id == match_id:
                    return match
            else:
                return None

    yield MockMatchRepository()


@pytest.fixture
def mock_prediction_repo(prediction1: PredictionModel, upcoming_match: MatchModel) -> BasePredictionRepository:
    class MockPredictionRepository(BasePredictionRepository):
        predictions = [prediction1]

        async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> list[PredictionModel]:
            predictions = []

            for prediction in self.predictions:
                if all(
                        (
                                prediction.match_id == upcoming_match.id,
                                prediction.user_id == user_id,
                                upcoming_match.event_id == event_id,
                        ),
                ):
                    predictions.append(prediction)

            return predictions

        async def get_by_id(self, prediction_id: int) -> PredictionModel | None:
            return await self._get_by_id(prediction_id=prediction_id)

        async def create(self, prediction: PredictionCreate, user_id: UUID) -> PredictionModel:
            return PredictionModel(**prediction.dict(), user_id=user_id)

        async def update(self, prediction_id: int, prediction_data: PredictionUpdate) -> PredictionModel | None:
            prediction = await self._get_by_id(prediction_id=prediction_id)

            if prediction is None:
                return None

            prediction.home_goals = prediction_data.home_goals
            prediction.away_goals = prediction_data.away_goals

            return prediction

        async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
            for prediction in self.predictions:
                if prediction.user_id == user_id and prediction.match_id == match_id:
                    return True
            else:
                return False

        async def update_points_for_match(self, match: MatchRead) -> None:
            pass

        async def _get_by_id(self, prediction_id: int) -> PredictionModel | None:
            for prediction in self.predictions:
                if prediction.id == prediction_id:
                    return prediction
            else:
                return None

    yield MockPredictionRepository()
