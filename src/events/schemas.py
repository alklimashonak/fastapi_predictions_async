from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    name: str | None = None
    status: int | None = None
    deadline: datetime | None = None


class MatchBase(BaseModel):
    home_team: str | None = None
    away_team: str | None = None
    status: int | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    start_time: datetime | None = None


class MatchCreate(MatchBase):
    home_team: str = Field(max_length=128)
    away_team: str = Field(max_length=128)
    start_time: datetime = Field(default=datetime.utcnow()+timedelta(days=1))


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    status: int = Field(default=0)
    deadline: datetime = Field(default=datetime.utcnow()+timedelta(days=1))
    matches: list[MatchCreate] = []


class MatchRead(MatchBase):
    id: int
    home_team: str
    away_team: str
    status: int
    home_goals: int | None
    away_goals: int | None
    start_time: datetime
    event_id: int

    class Config:
        orm_mode = True


class EventRead(EventBase):
    id: int
    name: str
    status: int
    deadline: datetime
    matches: list[MatchRead]

    class Config:
        orm_mode = True
