from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class MatchBase(BaseModel):
    home_team: str | None = None
    away_team: str | None = None
    status: int | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    start_time: datetime | None = None


class MatchCreate(BaseModel):
    home_team: str = Field(max_length=128, min_length=3)
    away_team: str = Field(max_length=128, min_length=3)
    start_time: datetime = Field(default=datetime.utcnow()+timedelta(days=1))


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
