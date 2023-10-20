from src.events.models import Match
from src.events.schemas import MatchCreate
from src.matches.schemas import MatchRead, MatchUpdate


class BaseMatchRepository:
    async def create(self, match: MatchCreate, event_id: int) -> Match:
        raise NotImplementedError

    async def get_by_id(self, match_id: int) -> Match | None:
        raise NotImplementedError

    async def update(self, match_id: int, match: MatchUpdate) -> Match:
        raise NotImplementedError

    async def delete(self, match_id: int) -> None:
        raise NotImplementedError


class BaseMatchService:
    async def create(self, match: MatchCreate, event_id: int) -> MatchRead:
        raise NotImplementedError

    async def delete(self, match_id: int) -> None:
        raise NotImplementedError
