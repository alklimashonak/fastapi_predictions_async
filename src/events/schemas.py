from datetime import datetime

from pydantic import BaseModel, Field

from src.events.models import EventStatus, MatchStatus


class EventBase(BaseModel):
    name: str | None = None
    status: EventStatus | None = None
    start_time: datetime | None = None


class MatchBase(BaseModel):
    team1: str | None = None
    team2: str | None = None
    status: MatchStatus | None = None
    team1_goals: int | None = None
    team2_goals: int | None = None
    start_time: datetime | None = None


class MatchCreate(MatchBase):
    team1: str = Field(max_length=128)
    team2: str = Field(max_length=128)
    status: MatchStatus = Field(default=MatchStatus.not_started)
    team1_goals: int | None = None
    team2_goals: int | None = None
    start_time: datetime


class MatchUpdate(MatchBase):
    id: int
    team1: str = Field(max_length=128)
    team2: str = Field(max_length=128)
    status: MatchStatus = Field(default=MatchStatus.not_started)
    team1_goals: int | None = None
    team2_goals: int | None = None
    start_time: datetime


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    status: EventStatus = Field(default=EventStatus.not_started)
    start_time: datetime
    matches: list[MatchCreate] = []


class EventUpdate(EventBase):
    name: str = Field(max_length=128)
    status: EventStatus = Field(default=EventStatus.not_started)
    start_time: datetime
    new_matches: list[MatchCreate] = []
    matches_to_update: list[MatchUpdate] = []
    matches_to_delete: list[int] = []


class MatchSchema(MatchBase):
    id: int
    team1: str
    team2: str
    status: MatchStatus
    team1_goals: int | None
    team2_goals: int | None
    start_time: datetime

    class Config:
        orm_mode = True


class EventSchema(EventBase):
    id: int
    name: str
    status: EventStatus
    start_time: datetime
    matches: list[MatchSchema]

    class Config:
        orm_mode = True
