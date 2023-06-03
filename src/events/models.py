import datetime
import enum
from typing import Protocol, TypeVar

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from src.database import Base


class MatchProtocol(Protocol):
    id: int
    team1: str
    team2: str
    status: int
    team1_goals: int
    team2_goals: int
    start_time: datetime.datetime


MP = TypeVar('MP', bound=MatchProtocol)


class EventProtocol(Protocol):
    id: int
    name: str
    start_time: datetime.datetime
    matches: list[MP]


EP = TypeVar('EP', bound=EventProtocol)


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    start_time = Column(DateTime(timezone=True))

    matches = relationship('Match', cascade='all,delete-orphan', backref='event')


class MatchStatus(enum.IntEnum):
    not_started = 0
    in_process = 1
    finished = 2


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, index=True)
    team1 = Column(String(128), nullable=False)
    team2 = Column(String(128), nullable=False)
    status = Column(pgEnum(MatchStatus), default=MatchStatus.not_started, nullable=False)
    team1_goals = Column(Integer, nullable=True, default=None)
    team2_goals = Column(Integer, nullable=True, default=None)
    start_time = Column(DateTime(timezone=True))

    event_id = Column(Integer, ForeignKey('events.id', ondelete='CASCADE'))
