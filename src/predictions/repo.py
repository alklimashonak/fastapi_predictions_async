from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.events.models import Match
from src.matches.schemas import MatchRead
from src.predictions.base import BasePredictionRepository
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate, PredictionUpdate


class PredictionRepository(BasePredictionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, prediction_id: int) -> Prediction | None:
        stmt = select(Prediction).where(Prediction.id == prediction_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multiple_by_event_id(self, event_id: int, user_id: UUID) -> Sequence[Prediction]:
        stmt = select(Prediction) \
            .join(Prediction.match) \
            .options(joinedload(Prediction.match)) \
            .filter(Prediction.user_id == user_id) \
            .filter(Match.event_id == event_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, prediction: PredictionCreate, user_id: UUID) -> Prediction:
        new_prediction = Prediction(**prediction.dict(), user_id=user_id)

        self.session.add(new_prediction)

        await self.session.commit()
        await self.session.refresh(new_prediction)

        return new_prediction

    async def update(self, prediction_id: int, prediction: PredictionUpdate) -> Prediction | None:
        stmt = update(Prediction).values(**prediction.dict()).where(Prediction.id == prediction_id).returning(
            Prediction)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.scalar_one_or_none()

    async def update_points_for_match(self, match: MatchRead) -> None:
        stmt1 = update(Prediction) \
            .where(
            (Prediction.match_id == match.id) &
            (Prediction.home_goals == match.home_goals) &
            (Prediction.away_goals == match.away_goals)
        ) \
            .values(points=3)

        if match.home_goals - match.away_goals > 0:
            stmt2 = update(Prediction) \
                .where(
                Prediction.points.is_(None) &
                Prediction.home_goals.is_not(None) &
                Prediction.away_goals.is_not(None) &
                (Prediction.match_id == match.id) &
                ((Prediction.home_goals - Prediction.away_goals) > 0)
            ) \
                .values(points=1)
        elif match.home_goals - match.away_goals < 0:
            stmt2 = update(Prediction) \
                .where(
                Prediction.points.is_(None) &
                Prediction.home_goals.is_not(None) &
                Prediction.away_goals.is_not(None) &
                (Prediction.match_id == match.id) &
                ((Prediction.home_goals - Prediction.away_goals) < 0)
            ) \
                .values(points=1)
        else:
            stmt2 = update(Prediction) \
                .where(
                Prediction.points.is_(None) &
                Prediction.home_goals.is_not(None) &
                Prediction.away_goals.is_not(None) &
                (Prediction.match_id == match.id) &
                ((Prediction.home_goals - Prediction.away_goals) == 0)
            ) \
                .values(points=1)

        stmt3 = update(Prediction).where(Prediction.points.is_(None) & (Prediction.match_id == match.id)).values(
            points=0)

        await self.session.execute(stmt1)
        await self.session.execute(stmt2)
        await self.session.execute(stmt3)

        await self.session.commit()

    async def exists_in_db(self, user_id: UUID, match_id: int) -> bool:
        stmt = select(Prediction).where(Prediction.user_id == user_id, Prediction.match_id == match_id)

        result = await self.session.execute(stmt)

        if result.scalar_one_or_none():
            return True
        return False
