import discord
import pytest

from cogs.GameProgressBot import GameProgressBot
from discord.ext import commands


def test_progress_bar_positive():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix='$', intents=intents)
    game_progress_bot = GameProgressBot(bot)
    actualProgress = game_progress_bot.progress_bar(20.0)
    assert "🟩 " * 2 + "⬜ " * 8 in actualProgress
