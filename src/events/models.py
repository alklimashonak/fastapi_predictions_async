import enum
from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from src.db.database import Base
from src.matches.models import Match


class EventStatus(enum.IntEnum):
    created = 0
    upcoming = 1
    ongoing = 2
    closed = 3
    completed = 4
    archived = 5
    cancelled = 6


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[EventStatus] = mapped_column(pgEnum(EventStatus), default=EventStatus.created, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    matches: Mapped[list['Match']] = relationship('Match', backref='event', lazy='selectin')
