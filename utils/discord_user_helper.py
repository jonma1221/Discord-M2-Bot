import discord

class DiscordUserHelper():
    def __init__(self, bot):
        self.bot = bot

    async def dm_user(self, user_id: int, message: str) -> bool:
        try:
            user = self.bot.get_user(user_id)
            if user is None:
                user = await self.bot.fetch_user(user_id)
            print(f"DM user - {user}")
            if user is not None:
                await user.send(message)
                return True
            return False
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return False
