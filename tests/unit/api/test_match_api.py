from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from src.auth.dependencies import get_current_user
from src.matches.dependencies import get_match_service
from src.matches.router import router as match_router
from tests.utils import EventModel, UserModel, MatchModel


@pytest.fixture
def app_factory():
    def _app_factory() -> FastAPI:
        app = FastAPI()
        app.include_router(match_router, prefix='', tags=['Matches'])

        return app

    return _app_factory


@pytest_asyncio.fixture
async def async_client(
        get_test_client, app_factory, fake_get_current_user, fake_get_match_service
) -> AsyncGenerator[AsyncClient, None]:
    app = app_factory()
    app.dependency_overrides[get_match_service] = fake_get_match_service
    app.dependency_overrides[get_current_user] = fake_get_current_user

    async for client in get_test_client(app):
        yield client


@pytest.mark.asyncio
class TestCreateMatch:
    json = {
        'home_team': 'Atalanta',
        'away_team': 'Bari',
        'start_time': '2023-09-20 10:27:21.240752',
    }

    async def test_missing_token(self, async_client: AsyncClient, created_event: EventModel) -> None:
        response = await async_client.post(
            f'/events/{created_event.id}/matches',
            json=self.json,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self,
            async_client: AsyncClient,
            active_user: UserModel,
            created_event: EventModel,
    ) -> None:
        response = await async_client.post(
            f'/events/{created_event.id}/matches', json=self.json, headers={'Authorization': active_user.email}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == "The user doesn't have enough privileges"

    async def test_superuser_has_access(self, async_client: AsyncClient,
                                        superuser: UserModel, created_event: EventModel) -> None:
        response = await async_client.post(
            f'/events/{created_event.id}/matches',
            json=self.json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['home_team'] == self.json.get('home_team')

    async def test_event_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.post(
            '/events/987/matches',
            json=self.json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Event not found'

    async def test_event_already_is_running(
            self, async_client: AsyncClient, superuser: UserModel, upcoming_event: EventModel
    ) -> None:
        response = await async_client.post(
            f'/events/{upcoming_event.id}/matches',
            json=self.json,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Event already is running'

    @pytest.mark.skip
    async def test_too_short_team_name_raises_422(self, async_client: AsyncClient,
                                                  superuser: UserModel, event1: EventModel) -> None:
        invalid_data = {
            'home_team': '',
            'away_team': '',
            'start_data': '2023-09-20 10:27:21.240752',
        }

        response = await async_client.post(
            f'/events/{event1.id}/matches',
            json=invalid_data,
            headers={'Authorization': superuser.email}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestFinishMatch:
    async def test_missing_token(self, async_client: AsyncClient, ongoing_match: MatchModel) -> None:
        response = await async_client.patch(
            f'/matches/{ongoing_match.id}/finish?home_goals=4&away_goals=4',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self, async_client: AsyncClient, active_user: UserModel, ongoing_match: MatchModel
    ) -> None:
        response = await async_client.patch(
            f'/matches/{ongoing_match.id}/finish?home_goals=4&away_goals=4',
            headers={'Authorization': active_user.email},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(
            self,
            async_client: AsyncClient,
            superuser: UserModel,
            ongoing_match: MatchModel,
    ) -> None:
        response = await async_client.patch(
            f'/matches/{ongoing_match.id}/finish',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_match_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.patch(
            '/matches/987/finish',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Match not found'

    async def test_match_has_not_started(
            self, async_client: AsyncClient, upcoming_match: MatchModel, superuser: UserModel
    ) -> None:
        response = await async_client.patch(
            f'/matches/{upcoming_match.id}/finish',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Match has not started yet'

    async def test_match_already_is_completed(
            self, async_client: AsyncClient, completed_match: MatchModel, superuser: UserModel
    ) -> None:
        response = await async_client.patch(
            f'/matches/{completed_match.id}/finish',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Match is already completed'


@pytest.mark.asyncio
class TestDeleteMatch:
    async def test_missing_token(self, async_client: AsyncClient, ongoing_match: MatchModel) -> None:
        response = await async_client.delete(
            f'/matches/{ongoing_match.id}',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == 'Not authenticated'

    async def test_active_user_has_not_access(
            self, async_client: AsyncClient, active_user: UserModel, ongoing_match: MatchModel
    ) -> None:
        response = await async_client.delete(
            f'/matches/{ongoing_match.id}',
            headers={'Authorization': active_user.email},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_superuser_has_access(
            self,
            async_client: AsyncClient,
            superuser: UserModel,
            ongoing_match: MatchModel,
    ) -> None:
        response = await async_client.delete(
            f'/matches/{ongoing_match.id}',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_match_not_found(self, async_client: AsyncClient, superuser: UserModel) -> None:
        response = await async_client.delete(
            '/matches/987',
            params={'home_goals': 4, 'away_goals': 4},
            headers={'Authorization': superuser.email},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == 'Match not found'
