import argparse
import asyncio
import os
from typing import Optional

import discord


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable {name}. "
            f"Set it before running, e.g. PowerShell: $env:{name}='VALUE_HERE'"
        )
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and print details for a Discord server (guild) by ID."
    )
    parser.add_argument(
        "guild_id",
        nargs="?",
        help="Guild (server) ID. If omitted, DISCORD_GUILD_ID will be used.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max members to print (0 = no limit).",
    )
    parser.add_argument(
        "--include-bots",
        action="store_true",
        help="Include bot accounts (bots are skipped by default).",
    )
    return parser.parse_args()


def _as_int_guild_id(raw: str) -> int:
    raw = raw.strip()
    if not raw.isdigit():
        raise SystemExit(f"guild_id must be a numeric ID, got: {raw!r}")
    return int(raw)


async def _resolve_guild(client: discord.Client, guild_id: int) -> Optional[discord.Guild]:
    cached = client.get_guild(guild_id)
    if cached is not None:
        return cached

    try:
        # Returns a Guild object even if it's not in cache, but may have limited fields.
        return await client.fetch_guild(guild_id, with_counts=True)
    except discord.Forbidden:
        print("Forbidden: bot can’t access that guild (is it in the server?).")
        return None
    except discord.NotFound:
        print("Not found: no guild with that ID (or bot can’t see it).")
        return None


def _print_guild_details(guild: discord.Guild) -> None:
    print("=== Guild Details ===")
    print(f"Name: {guild.name}")
    print(f"ID: {guild.id}")
    print(f"Created: {guild.created_at.isoformat() if guild.created_at else 'Unknown'}")
    print(f"Description: {guild.description!r}")
    print(f"Verification level: {getattr(guild.verification_level, 'name', guild.verification_level)}")
    print(f"MFA level: {getattr(guild.mfa_level, 'name', guild.mfa_level)}")
    print(f"NSFW level: {getattr(guild.nsfw_level, 'name', guild.nsfw_level)}")
    print(f"Premium tier: {getattr(guild.premium_tier, 'name', guild.premium_tier)}")
    print(f"Premium subscriptions: {getattr(guild, 'premium_subscription_count', None)}")
    print(f"Approx member count: {getattr(guild, 'approximate_member_count', None)}")
    print(f"Approx presence count: {getattr(guild, 'approximate_presence_count', None)}")
    print(f"Icon: {guild.icon.url if guild.icon else None}")
    print(f"Banner: {guild.banner.url if guild.banner else None}")

    owner_id = getattr(guild, "owner_id", None)
    print(f"Owner ID: {owner_id}")

    # These are only populated when the guild is in cache.
    if getattr(guild, "channels", None):
        text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
        categories = [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]
        threads = getattr(guild, "threads", [])
        print(f"Channels: {len(guild.channels)} total ({len(categories)} categories, {len(text_channels)} text, {len(voice_channels)} voice)")
        print(f"Threads: {len(threads)}")
        print(f"Roles: {len(getattr(guild, 'roles', []) or [])}")
    else:
        print("Channels/Roles: unavailable (guild not cached; invite the bot and enable guild intents).")


async def _print_members(guild: discord.Guild, *, limit: int, include_bots: bool) -> None:
    if limit < 0:
        raise SystemExit("--limit must be >= 0")

    print("=== Members ===")
    printed = 0
    bots_skipped = 0

    try:
        async for member in guild.fetch_members(limit=None):
            if (not include_bots) and member.bot:
                bots_skipped += 1
                continue

            # Prefer the server nickname / display name when available.
            name = member.display_name
            global_name = getattr(member, "global_name", None)
            username = member.name
            discriminator = getattr(member, "discriminator", "0")
            tag = username if discriminator in (None, "0") else f"{username}#{discriminator}"

            print(f"{member.id}\t{name}\t({tag}{' / ' + global_name if global_name else ''})")
            printed += 1

            if limit and printed >= limit:
                break
    except discord.Forbidden:
        print("Forbidden: missing permissions and/or Server Members Intent is not enabled.")
        return

    if bots_skipped:
        print(f"(skipped {bots_skipped} bot accounts; pass --include-bots to include them)")
    print(f"Total listed: {printed}")


async def main() -> None:
    args = _parse_args()
    guild_id_raw = args.guild_id or os.getenv("DISCORD_GUILD_ID")
    if not guild_id_raw:
        raise SystemExit(
            "Provide a guild ID as an argument or set DISCORD_GUILD_ID.\n"
            "Example: python fetch_guild_details.py 123456789012345678"
        )

    token = _require_env("DISCORD_TOKEN")
    guild_id = _as_int_guild_id(guild_id_raw)

    intents = discord.Intents.none()
    intents.guilds = True
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            guild = await _resolve_guild(client, guild_id)
            if guild is not None:
                _print_guild_details(guild)
                await _print_members(guild, limit=args.limit, include_bots=args.include_bots)
        finally:
            await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
