from typing import Any, Dict, List, Optional, Tuple

import discord


def as_int_guild_id(raw: str) -> int:
    """Parse a guild (server) ID from user/env input.

    Args:
        raw: A string containing a numeric Discord guild ID.

    Returns:
        The guild ID as an int.

    Raises:
        ValueError: If the input is not a numeric ID.
    """
    raw = raw.strip()
    if not raw.isdigit():
        raise ValueError(f"guild_id must be a numeric ID, got: {raw!r}")
    return int(raw)


async def resolve_guild_for_id(client: discord.Client, guild_id: int) -> Optional[discord.Guild]:
    """Resolve a `discord.Guild` by ID using cache first, then an API fetch.

    Notes:
        - This will only succeed if the bot can access the guild (typically: the bot is in it).
        - `client.fetch_guild(...)` can return a guild object with limited fields compared to a fully-cached guild.

    Args:
        client: The logged-in `discord.Client`.
        guild_id: The target guild ID.

    Returns:
        The resolved `discord.Guild`, or `None` if forbidden/not found.
    """
    guild = client.get_guild(guild_id)
    if guild is not None:
        return guild

    try:
        return await client.fetch_guild(guild_id)
    except (discord.Forbidden, discord.NotFound):
        return None


async def guild_members_data(guild: discord.Guild) -> Dict[str, Any]:
    """Fetch and normalize non-bot members for a guild into a plain Python dict.

    This uses `guild.fetch_members(...)`, so it requires:
        - the bot to have the Server Members Intent enabled (Developer Portal + code),
        - the bot to be in the guild and allowed to view members.

    Returns:
        A dict shaped like:
            {
              "guild": {"id": int, "name": str},
              "member_count": int,
              "members": [{"id": int, "display_name": str, "username": str}, ...]
            }
    """
    members: List[Dict[str, Any]] = []
    member_index: Dict[int, Dict[str, Any]] = {}
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue

        discriminator = getattr(member, "discriminator", "0")
        tag = member.name if discriminator in (None, "0") else f"{member.name}#{discriminator}"
        entry: Dict[str, Any] = {
            "id": member.id,
            "display_name": member.display_name,
            "username": tag,
            # Cached extras (populated/updated by the bot runtime):
            "dm_channel_id": None,
            "voice_channel_id": None,
        }
        members.append(entry)
        member_index[member.id] = entry

    return {
        "guild": {"id": guild.id, "name": guild.name},
        "member_count": len(members),
        "members": members,
        "member_index": member_index,
    }


async def resolve_member_for_id(
    guild: discord.Guild, user_id: int
) -> Tuple[Optional[discord.Member], Optional[str]]:
    """Resolve a `discord.Member` for a given guild/user pair.

    This is a best-effort helper that:
        - checks the local cache via `guild.get_member(user_id)` first,
        - falls back to an API call with `await guild.fetch_member(user_id)`.

    Args:
        guild: The guild the user is expected to belong to.
        user_id: The target user ID.

    Returns:
        A tuple of `(member, error)`:
            - `member` is a `discord.Member` when resolution succeeded; otherwise `None`.
            - `error` is `None` on success; otherwise a short string describing the failure.
    """
    cached = guild.get_member(user_id)
    if cached is not None:
        return cached, None

    try:
        fetched = await guild.fetch_member(user_id)
        return fetched, None
    except discord.Forbidden:
        return None, "forbidden"
    except discord.NotFound:
        return None, "not_found"
    except discord.HTTPException:
        return None, "http_exception"


def voice_state_error(member: discord.Member) -> Optional[str]:
    """Check a member's voice state and return an error string on failure.

    Per the requested behavior, any inability to confirm a member is in a voice
    channel is treated as an \"error\" condition.

    Args:
        member: A resolved `discord.Member`.

    Returns:
        None if voice state is present and has a channel; otherwise a short error string.
    """
    voice = getattr(member, "voice", None)
    if voice is None:
        return "voice_state_missing"
    if getattr(voice, "channel", None) is None:
        return "not_in_voice"
    return None

