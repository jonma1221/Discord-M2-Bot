
import discord
from discord.ext import commands

class BotCommands():
    def __init__(self, intents):
        self.bot = commands.Bot(command_prefix='$', intents=intents)
        
        @self.bot.hybrid_command(name="first_slash")
        async def first_slash(ctx): 
            await ctx.send("You executed the slash command!")