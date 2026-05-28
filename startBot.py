import os
import platform
import asyncio
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