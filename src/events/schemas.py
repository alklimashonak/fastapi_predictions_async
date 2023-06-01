from datetime import datetime

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    name: str | None = None
    start_time: datetime | None = None


class MatchBase(BaseModel):
    team1: str | None = None
    team2: str | None = None
    status: int | None = None
    team1_goals: int | None = None
    team2_goals: int | None = None
    start_time: datetime | None = None


class MatchCreate(MatchBase):
    team1: str = Field(max_length=128)
    team2: str = Field(max_length=128)
    status: int = Field(default=0)
    team1_goals: int | None = None
    team2_goals: int | None = None
    start_time: datetime


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    start_time: datetime
    matches: list[MatchCreate] = []


class EventUpdate(EventBase):
    name: str = Field(max_length=128)
    start_time: datetime
    matches: list[MatchCreate] = []
    matches_to_delete: list[int] = []


class MatchSchema(MatchBase):
    id: int
    team1: str
    team2: str
    status: int
    team1_goals: int | None
    team2_goals: int | None
    start_time: datetime

    class Config:
        orm_mode = True


class EventSchema(EventBase):
    id: int
    name: str
    start_time: datetime
    matches: list[MatchSchema]

    class Config:
        orm_mode = True
