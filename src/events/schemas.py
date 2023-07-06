from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from src.events.models import Status, MatchStatus


class EventBase(BaseModel):
    name: str | None = None
    status: Status | None = None
    deadline: datetime | None = None


class MatchBase(BaseModel):
    home_team: str | None = None
    away_team: str | None = None
    status: MatchStatus | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    start_time: datetime | None = None


class MatchCreate(MatchBase):
    home_team: str = Field(max_length=128)
    away_team: str = Field(max_length=128)
    start_time: datetime = Field(default=datetime.utcnow()+timedelta(days=1))


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    status: Status = Field(default=Status.not_started)
    deadline: datetime = Field(default=datetime.utcnow()+timedelta(days=1))
    matches: list[MatchCreate] = []


class MatchRead(MatchBase):
    id: int
    home_team: str
    away_team: str
    status: MatchStatus
    home_goals: int | None
    away_goals: int | None
    start_time: datetime

    class Config:
        orm_mode = True


class EventRead(EventBase):
    id: int
    name: str
    status: Status
    deadline: datetime
    matches: list[MatchRead]

    class Config:
        orm_mode = True
