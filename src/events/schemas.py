from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from src.events.models import EventStatus
from src.matches.schemas import MatchCreate, MatchRead


class EventBase(BaseModel):
    name: str | None = None
    deadline: datetime | None = None


class EventCreate(EventBase):
    name: str = Field(max_length=128)
    deadline: datetime = Field(default=datetime.utcnow()+timedelta(days=1))


class EventUpdate(EventBase):
    name: str = Field(max_length=128)
    deadline: datetime
    status: EventStatus


class EventRead(EventBase):
    id: int
    name: str
    status: int
    deadline: datetime
    matches: list[MatchRead]

    class Config:
        orm_mode = True
