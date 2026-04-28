import os
import asyncio
import discord
import bot_commands
import utils.discord_user_helper
import gemini_ai_text_prompt
import str_formatter

from discord.ext import commands
from typing import Any, Dict, List, Optional
from guild_data_helper import (
    as_int_guild_id,
    getGuildMembers,
    getGuild,
    resolve_member_for_id,
    printMembers
)
from yt_dl_helper import (
    playYoutubeAudio
)
from dotenv import load_dotenv

load_dotenv()

discord_token = os.getenv("DISCORD_TOKEN")
guild_id_raw = os.getenv("DISCORD_GUILD_ID")

# This example requires the 'message_content' intent.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)
# bot = commands.Bot(command_prefix='$', intents=intents)
botCommands = bot_commands.BotCommands(intents).bot
discordUserHelper = utils.discord_user_helper.DiscordUserHelper(client)
connectedGuilds = {}
guild_member_data: Dict[int, Dict[str, Any]] = {}

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
                # dm_sent = await _dm_user(user_id, "Hop on, it's time to start!")
                dm_sent = await discordUserHelper.dm_user(user_id, "Hop on, it's time to start!")
                if dm_sent:
                    nudged += 1
                    print(f"DM sent to {m['username']}")
                    # Cache DM channel id if we have it.
                    user_obj = client.get_user(user_id)
                    if user_obj is not None and getattr(user_obj, "dm_channel", None) is not None:
                        if isinstance(entry, dict):
                            entry["dm_channel_id"] = user_obj.dm_channel.id

        print(f"Nudge scan complete for guild {guild.id}. DMs sent: {nudged}")
    except Exception as e:
        print(f"Nudge scan crashed for guild {guild.id}: {e!r}")

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    # Get the voice channel by ID
    # channel = client.get_channel(1494790482763583591)  # Replace with your channel ID
    # print(f"Get channel details: {channel}")
    # voice_client = await channel.connect()
    # print(f"Connected to voice channel: {voice_client}")
    # playYoutubeAudio(voice_client)

    if not guild_id_raw:
        return

    try:
        guild_id = as_int_guild_id(guild_id_raw)
    except ValueError as e:
        print(f"Invalid DISCORD_GUILD_ID: {e}")
        return

    guild = await getGuild(client, guild_id)
    print(f"Guild: {guild.members}")
    if guild is None:
        print("Could not access guild from DISCORD_GUILD_ID (not found or forbidden).")
        return
    connectedGuilds[guild_id] = guild

    try:
        data = await getGuildMembers(guild)
    except discord.Forbidden:
        print("Forbidden listing members: enable Server Members Intent and ensure bot access.")
        return

    guild_member_data[guild.id] = data
    print(f"Cached {data['member_count']} members for guild {guild.name} ({guild.id}).")
    printMembers(guild.id, connectedGuilds)


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

client.run(discord_token)

