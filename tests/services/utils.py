import dataclasses
from datetime import datetime
from itertools import count
from uuid import UUID, uuid4

from src.events.models import Status as EventStatus
from src.matches.models import Status as MatchStatus


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
    status: EventStatus = EventStatus.not_started
    home_goals: int | None = None
    away_goals: int | None = None
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class EventModel:
    name: str
    deadline: datetime
    matches: list[MatchModel] = dataclasses.field(default_factory=lambda: [])
    status: MatchStatus = MatchStatus.not_started
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))


@dataclasses.dataclass
class PredictionModel:
    home_goals: int
    away_goals: int
    match_id: int
    user_id: UUID
    id: int = dataclasses.field(default_factory=lambda counter=count(): next(counter))
