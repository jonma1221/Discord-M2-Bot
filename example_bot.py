import os
import json
import asyncio
import yt_dlp
import discord
import bot_commands

from discord.ext import commands
from typing import Any, Dict, List, Optional
from guild_data import (
    as_int_guild_id,
    guild_members_data,
    resolve_guild_for_id,
    resolve_member_for_id,
)
import gemini_ai_text_prompt
import str_formatter


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable {name}. "
            f"Set it before running, e.g. PowerShell: $env:{name}='YOUR_TOKEN_HERE'"
        )
    return value


# This example requires the 'message_content' intent.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)
# bot = commands.Bot(command_prefix='$', intents=intents)
botCommands = bot_commands.BotCommands(intents).bot

guild_member_data: Dict[int, Dict[str, Any]] = {}

async def _dm_user(user_id: int, message: str) -> bool:
    try:
        user = client.get_user(user_id)
        if user is None:
            user = await client.fetch_user(user_id)
        await user.send(message)
        return True
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        return False


async def _scan_guild_and_nudge(guild: discord.Guild, *, skip_user_id: int) -> None:
    try:
        cached = guild_member_data.get(guild.id)
        if not cached:
            print(f"No cached guild_member_data for guild_id={guild.id}; skipping nudge scan.")
            return

        members = cached.get("members", [])
        member_index = cached.get("member_index", {})
        nudged = 0

        for m in members:
            user_id = m.get("id")
            if not isinstance(user_id, int):
                continue
            # if user_id == skip_user_id:
            #     continue

            # Voice state is cached by discord.py when voice_states intent is enabled.
            # Treat any missing/unavailable voice state as an "error" per requirements.
            # voice_state = guild.voice_states.get(user_id)
            # voice_channel = getattr(voice_state, "channel", None) if voice_state else None
                    
            member, error = await resolve_member_for_id(guild, user_id)
            voice_channel = getattr(member, "voice", None)
            # Keep cached voice_channel_id updated (best-effort).
            entry = member_index.get(user_id) if isinstance(member_index, dict) else None
            if isinstance(entry, dict):
                entry["voice_channel_id"] = getattr(voice_channel, "id", None)

            if voice_channel is None:
                dm_sent = await _dm_user(user_id, "Hop on, it's time to start!")
                if dm_sent:
                    nudged += 1
                    # Cache DM channel id if we have it.
                    user_obj = client.get_user(user_id)
                    if user_obj is not None and getattr(user_obj, "dm_channel", None) is not None:
                        if isinstance(entry, dict):
                            entry["dm_channel_id"] = user_obj.dm_channel.id

        print(f"Nudge scan complete for guild {guild.id}. DMs sent: {nudged}")
    except Exception as e:
        print(f"Nudge scan crashed for guild {guild.id}: {e!r}")


def _print_cached_members(guild_id: int) -> None:
    data = guild_member_data.get(guild_id)
    if not data:
        print(f"No cached members for guild_id={guild_id}.")
        return

    guild_meta = data.get("guild", {})
    members = data.get("members", [])
    print(f"=== Members for {guild_meta.get('name')} ({guild_meta.get('id')}) ===")
    for m in members:
        print(f"{m.get('id')}\t{m.get('display_name')}\t{m.get('username')}")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    guild_id_raw = os.getenv("DISCORD_GUILD_ID")
    if not guild_id_raw:
        return

    try:
        guild_id = as_int_guild_id(guild_id_raw)
    except ValueError as e:
        print(f"Invalid DISCORD_GUILD_ID: {e}")
        return

    guild = await resolve_guild_for_id(client, guild_id)
    if guild is None:
        print("Could not access guild from DISCORD_GUILD_ID (not found or forbidden).")
        return

    try:
        data = await guild_members_data(guild)
    except discord.Forbidden:
        print("Forbidden listing members: enable Server Members Intent and ensure bot access.")
        return

    guild_member_data[guild.id] = data
    print(f"Cached {data['member_count']} members for guild {guild.name} ({guild.id}).")
    _print_cached_members(guild.id)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if len(message.mentions) == 1 and message.mentions[0].bot:
        print("This message is directed at a bot")
        result = await gemini_ai_text_prompt.execute_prompt_async(message.content)
        print("result: ", result)
        # sanitized_result = str_formatter.sanitize_text(result)
        # print("sanitized result: ", sanitized_result)
        # await message.channel.send(sanitized_result)

        for chunk in str_formatter.split_message(result):
            await message.reply(chunk)


@client.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    discriminator = getattr(member, "discriminator", "0")
    tag = member.name if discriminator in (None, "0") else f"{member.name}#{discriminator}"
    global_name = getattr(member, "global_name", None)
    roles_count = len(getattr(member, "roles", []) or [])

    def _is_voice_channel(channel: Optional[discord.abc.GuildChannel]) -> bool:
        """True for normal voice channels only (not stage)."""
        return isinstance(channel, discord.VoiceChannel)

    # Joined a voice channel: was not connected to guild voice before, now in a VoiceChannel.
    # (Mute/deafen/self-stream updates keep the same channel and won't match this.)
    if (
        not member.bot
        and before.channel is None
        and after.channel is not None
        and _is_voice_channel(after.channel)
    ):
        # Update cached voice_channel_id for this member.
        cached = guild_member_data.get(after.channel.guild.id)
        if cached and isinstance(cached.get("member_index"), dict):
            entry = cached["member_index"].get(member.id)
            if isinstance(entry, dict):
                entry["voice_channel_id"] = after.channel.id

        print(
            f"{tag} ({member.display_name}{' / ' + global_name if global_name else ''}) "
            f"joined voice: {after.channel.name} "
            f"(user_id={member.id}, bot={member.bot}, roles={roles_count}, "
            f"guild={after.channel.guild.name}, channel_id={after.channel.id})"
        )
        asyncio.create_task(
            _scan_guild_and_nudge(after.channel.guild, skip_user_id=member.id)
        )
        return

    # Moved between voice channels (still a "join" of the new channel)
    if (
        before.channel is not None
        and after.channel is not None
        and before.channel.id != after.channel.id
    ):
        print(
            f"{tag} ({member.display_name}{' / ' + global_name if global_name else ''}) "
            f"moved voice: {before.channel.name} -> {after.channel.name} "
            f"(user_id={member.id}, bot={member.bot}, roles={roles_count}, guild={after.channel.guild.name})"
        )


client.run(_require_env("DISCORD_TOKEN"))

