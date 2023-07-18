import enum
from datetime import datetime

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from src.db.database import Base
from src.predictions.models import Prediction


class Status(enum.IntEnum):
    not_started = 0
    in_process = 1
    finished = 2


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[Status] = mapped_column(pgEnum(Status), default=Status.not_started, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    matches: Mapped[list['Match']] = relationship('Match', backref='event')


class Match(Base):
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[Status] = mapped_column(pgEnum(Status), default=Status.not_started, nullable=False)
    home_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    event_id: Mapped[int] = mapped_column(Integer, ForeignKey('events.id', ondelete='CASCADE'))

    predictions: Mapped[list['Prediction']] = relationship('Prediction', backref='match')
