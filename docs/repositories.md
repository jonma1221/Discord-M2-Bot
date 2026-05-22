# Repositories

A generic, interface-driven API client module using the repository pattern.
Designed to work with any REST API provider. `SteamRepository` is the first implementation.

## Architecture

```
repositories/
├── __init__.py           # re-exports everything
├── SteamRepository.py    # ABC interface + implementation
└── steam_models.py       # dataclass response models
```

## ApiRepository (ABC)

Abstract base class defining the contract:

| Method | Signature |
|---|---|
| `get` | `async (endpoint, params=None) -> dict` |
| `post` | `async (endpoint, data=None) -> dict` |
| `request` | `async (method, endpoint, **kwargs) -> dict` |
| `close` | `async () -> None` |

## SteamRepository

Wraps `aiohttp.ClientSession`. Base URL: `https://api.steampowered.com`.
Appends `?key=<STEAM_API_KEY>` to every request automatically.

### Instantiation

```python
from repositories import SteamRepository

# reads STEAM_API_KEY from environment
steam = SteamRepository()

# or pass explicitly
steam = SteamRepository(api_key="xxx")
```

### Typed methods

| Method | Returns |
|---|---|
| `get_player_summaries(steam_ids)` | `GetPlayerSummariesResponse` |
| `get_friend_list(steam_id)` | `GetFriendListResponse` |
| `get_owned_games(steam_id)` | `GetOwnedGamesResponse` |

### Raw requests

The base class methods are also available for any endpoint:

```python
data = await steam.get("ISteamApp/GetAppList/v2/")
data = await steam.post("some/endpoint", data={...})
```

### Cleanup

```python
await steam.close()
```

## Models (`steam_models.py`)

Standard library `@dataclass` classes — no external dependencies.
Each model has a `from_dict(data: dict)` static factory for JSON parsing.

| Model | Fields |
|---|---|
| `PlayerAvatar` | `small`, `medium`, `large` |
| `PlayerSummary` | `steam_id`, `person_name`, `profile_url`, `avatar`, `time_created`, `real_name`, `country_code`, `state_code`, `city_id`, `game_count`, `game_server_ip`, `game_server_steam_id`, `game_extra_info`, `last_logoff`, `comment_permission` |
| `GetPlayerSummariesResponse` | `players: list[PlayerSummary]` |
| `Friend` | `steam_id`, `friend_since`, `relationship` |
| `GetFriendListResponse` | `friends: list[Friend]` |
| `Game` | `app_id`, `name`, `playtime_forever`, `playtime_2weeks`, `img_icon_url`, `img_logo_url`, `has_community_visible_stats` |
| `GetOwnedGamesResponse` | `game_count`, `games: list[Game]` |

## Environment

Add to `.env`:

```
STEAM_API_KEY=your_key_here
```

## Adding a new API provider

1. Create `repositories/<provider>_models.py` — dataclass models with `from_dict`
2. Create `repositories/<provider>_repository.py` — class extending `ApiRepository`
3. Export from `repositories/__init__.py`
