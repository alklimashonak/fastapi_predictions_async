import enum
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from src.db.database import Base
from src.predictions.models import Prediction


class MatchResult(enum.IntEnum):
    draw = 0
    home_win = 1
    away_win = 2


class MatchStatus(enum.IntEnum):
    upcoming = 0
    ongoing = 1
    completed = 2


class Match(Base):
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(pgEnum(MatchStatus), default=MatchStatus.upcoming, nullable=False)
    home_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    event_id: Mapped[int] = mapped_column(Integer, ForeignKey('events.id', ondelete='CASCADE'))

    predictions: Mapped[list['Prediction']] = relationship('Prediction', backref='match')

    def result(self) -> MatchResult | None:
        if not self.home_goals or not self.away_goals:
            return None
        elif self.home_goals == self.away_goals:
            return MatchResult.draw
        elif self.home_goals > self.away_goals:
            return MatchResult.home_win
        elif self.away_goals > self.home_goals:
            return MatchResult.away_win
