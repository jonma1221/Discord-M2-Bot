import discord
import gemini_ai_text_prompt
import str_formatter

from discord.ext import commands
from typing import Any, Dict, List, Optional

class GeminiAIBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if len(message.mentions) == 1 and message.mentions[0].bot:
            print("This message is directed at a bot")
            result = await gemini_ai_text_prompt.execute_prompt_async(message.content)
            print("result: ", result)

            for chunk in str_formatter.split_message(result):
                await message.reply(chunk)

    @commands.hybrid_command(name="send_ai_prompt", description="Ask AI bot", brief="Give a prompt to the bot to ask AI")
    async def send_ai_prompt(self, ctx, prompt):
        # await ctx.send(prompt)
        await ctx.defer()
        print("This message is directed at a bot")
        result = await gemini_ai_text_prompt.execute_prompt_async(prompt)
        print("result: ", result)

        for chunk in str_formatter.split_message(result):
            await ctx.reply(chunk)

async def setup(bot):
    await bot.add_cog(GeminiAIBot(bot))