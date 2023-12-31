from pydantic import BaseModel, UUID4


class PredictionBase(BaseModel):
    home_goals: int | None = None
    away_goals: int | None = None


class PredictionCreate(PredictionBase):
    home_goals: int
    away_goals: int
    match_id: int


class PredictionUpdate(PredictionBase):
    home_goals: int
    away_goals: int


class PredictionRead(PredictionBase):
    id: int | None = None
    points: int | None = None
    user_id: UUID4 | None = None
    match_id: int | None = None

    class Config:
        orm_mode = True
