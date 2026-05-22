from abc import ABC, abstractmethod
import os

import aiohttp

from repositories.steam_models import (
    GetFriendListResponse,
    GetOwnedGamesResponse,
    GetPlayerSummariesResponse,
    GetRecentlyPlayedGamesResponse,
)


class SteamRepositoryInterface(ABC):
    @abstractmethod
    async def get_player_summaries(
        self, steam_ids: str | list[str]
    ) -> GetPlayerSummariesResponse:
        ...

    @abstractmethod
    async def get_friend_list(
        self, steam_id: str
    ) -> GetFriendListResponse:
        ...

    @abstractmethod
    async def get_owned_games(
        self,
        steam_id: str,
        include_appinfo: bool = True,
        include_played_free_games: bool = False,
    ) -> GetOwnedGamesResponse:
        ...

    @abstractmethod
    async def get_recently_played_games(
        self,
        steam_id: str,
        count: int | None = None,
    ) -> GetRecentlyPlayedGamesResponse:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class SteamRepository(SteamRepositoryInterface):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.steampowered.com",
        session: aiohttp.ClientSession | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or os.getenv("STEAM_API_KEY", "")
        self._session = session

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _build_url(self, endpoint: str) -> str:
        sep = "&" if "?" in endpoint else "?"
        return f"{self._base_url}/{endpoint}{sep}key={self._api_key}"

    async def get(self, endpoint: str, params: dict | None = None) -> dict:
        session = await self._ensure_session()
        url = self._build_url(endpoint)
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post(self, endpoint: str, data: dict | None = None) -> dict:
        session = await self._ensure_session()
        url = self._build_url(endpoint)
        async with session.post(url, json=data) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict:
        session = await self._ensure_session()
        url = self._build_url(endpoint)
        async with session.request(method, url, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # -- typed helpers --

    async def get_player_summaries(
        self, steam_ids: str | list[str]
    ) -> GetPlayerSummariesResponse:
        if isinstance(steam_ids, list):
            steam_ids = ",".join(steam_ids)
        data = await self.get(
            "ISteamUser/GetPlayerSummaries/v2/",
            params={"steamids": steam_ids},
        )
        return GetPlayerSummariesResponse.from_dict(data)

    async def get_friend_list(
        self, steam_id: str
    ) -> GetFriendListResponse:
        data = await self.get(
            "ISteamUser/GetFriendList/v1/",
            params={"steamid": steam_id},
        )
        return GetFriendListResponse.from_dict(data)

    async def get_owned_games(
        self,
        steam_id: str,
        include_appinfo: bool = True,
        include_played_free_games: bool = False,
    ) -> GetOwnedGamesResponse:
        data = await self.get(
            "IPlayerService/GetOwnedGames/v1/",
            params={
                "steamid": steam_id,
                "include_appinfo": int(include_appinfo),
                "include_played_free_games": int(include_played_free_games),
            },
        )
        return GetOwnedGamesResponse.from_dict(data)

    async def get_recently_played_games(
        self,
        steam_id: str,
        count: int | None = None,
    ) -> GetRecentlyPlayedGamesResponse:
        params = {"steamid": steam_id}
        if count is not None:
            params["count"] = str(count)
        data = await self.get(
            "IPlayerService/GetRecentlyPlayedGames/v1/",
            params=params,
        )
        return GetRecentlyPlayedGamesResponse.from_dict(data)
