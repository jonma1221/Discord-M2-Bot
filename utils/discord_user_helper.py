import discord

class DiscordUserHelper():
    def __init__(self, client):
        self.client = client

    async def dm_user(self, user_id: int, message: str) -> bool:
        try:
            user = self.client.get_user(user_id)
            if user is None:
                user = await self.client.fetch_user(user_id)
            await user.send(message)
            return True
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return False
