import uuid

from sqlalchemy import Integer, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Prediction(Base):
    __tablename__ = 'predictions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    home_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    points: Mapped[int] = mapped_column(Integer, nullable=True, default=None)

    match_id: Mapped[int] = mapped_column(Integer, ForeignKey('matches.id', ondelete='CASCADE'))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey('users.id', ondelete='CASCADE'))