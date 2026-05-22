from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlayerAvatar:
    small: str = ""
    medium: str = ""
    large: str = ""

    @staticmethod
    def from_dict(data: dict) -> "PlayerAvatar":
        return PlayerAvatar(
            small=data.get("avatar", ""),
            medium=data.get("avatarmedium", ""),
            large=data.get("avatarfull", ""),
        )


@dataclass
class PlayerSummary:
    steam_id: str = ""
    person_name: str = ""
    profile_url: str = ""
    avatar: PlayerAvatar | None = None
    time_created: int = 0
    real_name: str = ""
    country_code: str = ""
    state_code: str = ""
    city_id: int = 0
    game_count: int = 0
    game_server_ip: str = ""
    game_server_steam_id: str = ""
    game_extra_info: str = ""
    last_logoff: int = 0
    comment_permission: bool = True

    @staticmethod
    def from_dict(data: dict) -> "PlayerSummary":
        avatar_data = PlayerAvatar.from_dict(data) if data.get("avatar") else None
        return PlayerSummary(
            steam_id=data.get("steamid", ""),
            person_name=data.get("personaname", ""),
            profile_url=data.get("profileurl", ""),
            avatar=avatar_data,
            time_created=data.get("timecreated", 0),
            real_name=data.get("realname", ""),
            country_code=data.get("loccountrycode", ""),
            state_code=data.get("locstatecode", ""),
            city_id=data.get("loccityid", 0),
            game_count=data.get("game_count", 0),
            game_server_ip=data.get("gameserverip", ""),
            game_server_steam_id=data.get("gameserversteamid", ""),
            game_extra_info=data.get("gameextrainfo", ""),
            last_logoff=data.get("lastlogoff", 0),
            comment_permission=bool(data.get("commentpermission", 1)),
        )


@dataclass
class GetPlayerSummariesResponse:
    players: list[PlayerSummary] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "GetPlayerSummariesResponse":
        raw = data.get("response", {}).get("players", [])
        return GetPlayerSummariesResponse(
            players=[PlayerSummary.from_dict(p) for p in raw]
        )


@dataclass
class Friend:
    steam_id: str = ""
    friend_since: int = 0
    relationship: str = ""

    @staticmethod
    def from_dict(data: dict) -> "Friend":
        return Friend(
            steam_id=data.get("steamid", ""),
            friend_since=data.get("friend_since", 0),
            relationship=data.get("relationship", ""),
        )


@dataclass
class GetFriendListResponse:
    friends: list[Friend] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "GetFriendListResponse":
        raw = data.get("friendslist", {}).get("friends", [])
        return GetFriendListResponse(
            friends=[Friend.from_dict(f) for f in raw]
        )


@dataclass
class Game:
    app_id: int = 0
    name: str = ""
    playtime_forever: int = 0
    playtime_2weeks: int = 0
    img_icon_url: str = ""
    img_logo_url: str = ""
    has_community_visible_stats: bool = False

    @property
    def icon_url(self) -> str:
        if self.img_icon_url:
            return (
                f"https://media.steampowered.com/steamcommunity/public/images/apps/"
                f"{self.app_id}/{self.img_icon_url}.jpg"
            )
        return ""

    @property
    def logo_url(self) -> str:
        if self.img_logo_url:
            return (
                f"https://media.steampowered.com/steamcommunity/public/images/apps/"
                f"{self.app_id}/{self.img_logo_url}.jpg"
            )
        return ""

    @staticmethod
    def from_dict(data: dict) -> "Game":
        return Game(
            app_id=data.get("appid", 0),
            name=data.get("name", ""),
            playtime_forever=data.get("playtime_forever", 0),
            playtime_2weeks=data.get("playtime_2weeks", 0),
            img_icon_url=data.get("img_icon_url", ""),
            img_logo_url=data.get("img_logo_url", ""),
            has_community_visible_stats=bool(
                data.get("has_community_visible_stats", False)
            ),
        )


@dataclass
class GetOwnedGamesResponse:
    game_count: int = 0
    games: list[Game] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "GetOwnedGamesResponse":
        resp = data.get("response", {})
        return GetOwnedGamesResponse(
            game_count=resp.get("game_count", 0),
            games=[Game.from_dict(g) for g in resp.get("games", [])],
        )


@dataclass
class GetRecentlyPlayedGamesResponse:
    total_count: int = 0
    games: list[Game] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "GetRecentlyPlayedGamesResponse":
        resp = data.get("response", {})
        return GetRecentlyPlayedGamesResponse(
            total_count=resp.get("total_count", 0),
            games=[Game.from_dict(g) for g in resp.get("games", [])],
        )
