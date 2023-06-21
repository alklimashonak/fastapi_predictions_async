import enum
from datetime import datetime

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from src.database import Base


class MatchStatus(enum.IntEnum):
    not_started = 0
    in_process = 1
    finished = 2


class EventStatus(enum.IntEnum):
    not_started = 0
    in_process = 1
    finished = 2


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[EventStatus] = mapped_column(pgEnum(EventStatus), default=EventStatus.not_started, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    matches: Mapped[list['Match']] = relationship('Match', cascade='all,delete-orphan', backref='event')


class Match(Base):
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team1: Mapped[str] = mapped_column(String(128), nullable=False)
    team2: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(pgEnum(MatchStatus), default=MatchStatus.not_started, nullable=False)
    team1_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    team2_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    event_id: Mapped[int] = mapped_column(Integer, ForeignKey('events.id', ondelete='CASCADE'))
