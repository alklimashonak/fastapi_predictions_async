import random
import dataclasses
from datetime import datetime
from itertools import count
from uuid import UUID, uuid4

from src.events.models import EventStatus
from src.matches.models import MatchStatus


user_password = 'user'
superuser_password = 'admin'


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
    status: MatchStatus = MatchStatus.upcoming
    home_goals: int | None = None
    away_goals: int | None = None
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class EventModel:
    name: str
    deadline: datetime
    matches: list[MatchModel] = dataclasses.field(default_factory=lambda: [])
    status: EventStatus = EventStatus.created
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class PredictionModel:
    home_goals: int
    away_goals: int
    match_id: int
    user_id: UUID
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))
    points: int | None = None


teams = ['Real Madrid', 'Barcelona', 'Liverpool', 'Arsenal', 'Juventus']


def gen_random_match(event_id: int):
    return MatchModel(
        id=random.randint(a=1, b=999),
        home_team=random.choice(teams),
        away_team=random.choice(teams),
        start_time=datetime.utcnow(),
        event_id=event_id,
    )


def gen_finished_match(event_id: int):
    return MatchModel(
        id=random.randint(a=1, b=999),
        home_team=random.choice(teams),
        away_team=random.choice(teams),
        start_time=datetime.utcnow(),
        event_id=event_id,
        status=MatchStatus.completed,
        home_goals=random.randint(a=0, b=9),
        away_goals=random.randint(a=0, b=9),
    )


def gen_matches(event_id: int, count: int, finished: bool = False):
    if finished:
        return [gen_finished_match(event_id=event_id) for i in range(count)]
    return [gen_random_match(event_id=event_id) for i in range(count)]
