import discord

from discord.ext import commands
from repositories.SteamRepository import SteamRepository
from repositories.steam_models import Game
from howlongtobeatpy import HowLongToBeat

class SteamActivityBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam = SteamRepository()

        # Map Discord user IDs to Steam IDs.
        self.steam_ids: dict[int, str] = {
            149361272650072064: "76561198005295234", # kami
            387764803420160004: "76561198055896064", # Allusiontensai
            180543227353497600: "76561198047018113" # coolname
        }

    @commands.hybrid_command(
        name="steam_activity",
        description="Show recently played games for registered users",
        brief="Show Steam recently played games",
    )
    async def steam_activity(self, ctx):
        await ctx.defer()

        guild = ctx.guild
        if not self.steam_ids:
            await ctx.reply("No Steam IDs configured yet.")
            return

        all_embeds: list[discord.Embed] = []

        for discord_id, steam_id in self.steam_ids.items():
            member = guild.get_member(discord_id)
            if member is None:
                continue

            try:
                response = await self.steam.get_recently_played_games(steam_id)
            except Exception as e:
                print(f"Failed to fetch games for {member.display_name}: {e}")
                continue

            if not response.games:
                continue

            for game in response.games:
                embed = discord.Embed(
                    title=game.name,
                    description=f"Playtime: {round(float(game.playtime_2weeks / 60), 1)} hours (last 2 weeks)",
                    color=discord.Color.blue(),
                )
                if game.icon_url:
                    embed.set_thumbnail(url=game.icon_url)
                embed.set_footer(
                    text=f"{member.display_name} ({member.name})",
                    icon_url=member.display_avatar.url,
                )
                all_embeds.append(embed)

        if not all_embeds:
            await ctx.reply("No recently played games found for any registered users.")
            return

        # Discord allows up to 10 embeds per message.
        for i in range(0, len(all_embeds), 10):
            batch = all_embeds[i : i + 10]
            await ctx.send(embeds=batch)


async def setup(bot):
    await bot.add_cog(SteamActivityBot(bot))
