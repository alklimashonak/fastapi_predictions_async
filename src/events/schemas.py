from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from src.matches.schemas import MatchCreate, MatchRead


class EventBase(BaseModel):
    name: str | None = None
    deadline: datetime | None = None


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    deadline: datetime = Field(default=datetime.utcnow()+timedelta(days=1))


class EventRead(EventBase):
    id: int
    name: str
    status: int
    deadline: datetime
    matches: list[MatchRead]

    class Config:
        orm_mode = True
