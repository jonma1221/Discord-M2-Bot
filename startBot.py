import os
import platform
import asyncio
import argparse
import discord
import discord.opus
if platform.system() == 'Darwin' and not discord.opus.is_loaded():
    discord.opus.load_opus('/opt/homebrew/lib/libopus.0.dylib')
import utils.discord_user_helper

from discord.ext import commands
from typing import Any, Dict, List, Optional
from guild_data_helper import (
    as_int_guild_id,
    getGuildMembers,
    getGuild,
    resolve_member_for_id,
    printMembers
)
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description="Discord M2 Bot")
parser.add_argument("--discord-token", help="Override DISCORD_TOKEN")
parser.add_argument("--discord-guild-id", help="Override DISCORD_GUILD_ID")
parser.add_argument("--steam-api-key", help="Override STEAM_API_KEY")
parser.add_argument("--gemini-api-key", help="Override GEMINI_API_KEY")
parser.add_argument("--env", action="append", metavar="KEY=VALUE",
                    help="Set an arbitrary env var (repeatable)")
args, _ = parser.parse_known_args()

_cli_env_map = {
    "discord_token": "DISCORD_TOKEN",
    "discord_guild_id": "DISCORD_GUILD_ID",
    "steam_api_key": "STEAM_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
}
for attr, env_key in _cli_env_map.items():
    value = getattr(args, attr)
    if value is not None:
        os.environ[env_key] = value

if args.env:
    for pair in args.env:
        key, _, value = pair.partition("=")
        if key and value:
            os.environ[key] = value

discord_token = os.getenv("DISCORD_TOKEN")
guild_id_raw = os.getenv("DISCORD_GUILD_ID")

# This example requires the 'message_content' intent.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)
bot.connectedGuilds = {}
bot.discordUserHelper = utils.discord_user_helper.DiscordUserHelper(bot)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    try:
        guild_id = as_int_guild_id(guild_id_raw)
    except ValueError as e:
        print(f"Invalid DISCORD_GUILD_ID: {e}")
        return

    guild = await getGuild(bot, guild_id)
    print(f"Guild: {guild.members}")
    if guild is None:
        print("Could not access guild from DISCORD_GUILD_ID (not found or forbidden).")
        return
    bot.connectedGuilds[guild_id] = guild

    try:
        data = await getGuildMembers(guild)
    except discord.Forbidden:
        print("Forbidden listing members: enable Server Members Intent and ensure bot access.")
        return

    print(f"Cached {data['member_count']} members for guild {guild.name} ({guild.id}).")
    printMembers(guild.id, bot.connectedGuilds)

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            ext = f'cogs.{filename[:-3]}'
            if ext not in bot.extensions:
                await bot.load_extension(ext)
                print(filename)
    
    synced = await bot.tree.sync()
    print(f"{len(synced)} commands synced to the the servers!")
    
bot.run(discord_token)