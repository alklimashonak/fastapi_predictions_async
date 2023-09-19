import random
from datetime import datetime

from tests.services.conftest import MatchModel

teams = ['Real Madrid', 'Barcelona', 'Liverpool', 'Arsenal', 'Juventus']


def gen_random_match(event_id: int):
    return MatchModel(
        id=random.randint(a=1, b=999),
        home_team=random.choice(teams),
        away_team=random.choice(teams),
        start_time=datetime.utcnow(),
        event_id=event_id,
    )


def gen_matches(event_id: int, count: int):
    return [gen_random_match(event_id=event_id) for i in range(count)]
