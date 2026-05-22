import discord

from discord.ext import commands
from typing import Any

from repositories.SteamRepository import SteamRepository
from howlongtobeatpy import HowLongToBeat


class GameProgressBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam = SteamRepository()
        self.hltb = HowLongToBeat()

        # Map Discord user IDs to Steam IDs.
        self.steam_ids: dict[int, str] = {
            149361272650072064: "76561198005295234",  # kami
            387764803420160004: "76561198055896064",  # Allusiontensai
            180543227353497600: "76561198047018113",  # coolname
        }

    async def cog_unload(self):
        await self.steam.close()

    @commands.hybrid_command(
        name="game_progress",
        description="Show completion progress for games the group plays together",
        brief="Game completion progress tracker",
    )
    async def game_progress(self, ctx):
        await ctx.defer()

        guild = ctx.guild
        if not self.steam_ids:
            await ctx.reply("No Steam IDs configured yet.")
            return

        # Fetch recently played games and build aggregated data.
        game_data: dict[str, dict[str, Any]] = {}
        active_discord_ids: list[int] = []

        for discord_id, steam_id in self.steam_ids.items():
            member = guild.get_member(discord_id)
            print(f"Member for {discord_id}: {member}")
            if member is None:
                continue

            try:
                response = await self.steam.get_recently_played_games(steam_id)
            except Exception as e:
                print(f"Failed to fetch games for {discord_id}: {e}")
                continue

            if not response.games:
                continue

            active_discord_ids.append(discord_id)

            for game in response.games:
                key = game.name.lower()
                if key not in game_data:
                    game_data[key] = {
                        "name": game.name,
                        "app_id": game.app_id,
                        "icon_url": game.icon_url,
                        "logo_url": game.logo_url,
                        "playtimes": {},
                        "members": [],
                    }
                game_data[key]["playtimes"][steam_id] = game.playtime_forever
                if discord_id not in game_data[key]["members"]:
                    game_data[key]["members"].append(discord_id)

        # if len(active_discord_ids) < 2:
        #     await ctx.reply("Not enough members with recently played games to compare.")
        #     return

        # Find games that appear in ALL active members' lists with playtime > 0.
        common_games = []
        for key, data in game_data.items():
            has_all_members = all(
                did in data["members"] for did in active_discord_ids
            )
            if not has_all_members:
                continue

            all_have_playtime = all(
                data["playtimes"].get(self.steam_ids[did], 0) > 0
                for did in active_discord_ids
            )
            if not all_have_playtime:
                continue

            common_games.append(data)
        print(f"Common games: {common_games}")
        if not common_games:
            await ctx.reply("No common games found.")
            return

        # Look up completion times via HowLongToBeat.
        group_progress = []

        for game_info in common_games:
            game_name = game_info["name"]

            try:
                hltb_results = await self.hltb.async_search(game_name)
            except Exception as e:
                print(f"HLTB search failed for {game_name}: {e}")
                continue

            if not hltb_results:
                continue

            found_match = None
            for entry in hltb_results:
                if entry.main_story is not None and entry.similarity > 0.5:
                    if found_match is None or entry.similarity > found_match.similarity:
                        found_match = entry

            if found_match is None or found_match.main_story == 0:
                continue

            min_playtime = min(game_info["playtimes"].values())
            hours = min_playtime / 60
            main_story_minutes = found_match.main_story * 60
            progress = min((min_playtime / main_story_minutes), 1.0) * 100

            group_progress.append({
                "name": game_name,
                "icon_url": game_info["icon_url"],
                "hours": hours,
                "main_story": found_match.main_story,
                "main_extra": found_match.main_extra,
                "completionist": found_match.completionist,
                "progress": progress,
            })

        if not group_progress:
            await ctx.reply("No common games with completion data found.")
            return

        all_embeds: list[discord.Embed] = []
        for gp in group_progress:
            embed = discord.Embed(
                title=f"{gp['name']}",
                color=discord.Color.green(),
            )
            if gp.get("icon_url"):
                embed.set_thumbnail(url=gp["icon_url"])
            embed.add_field(
                name="**Current Playtime**",
                value=f"{gp['hours']:.1f} hours\n",
                inline=True,
            )
            embed.add_field(
                name="**How Long To Beat**",
                value=(
                    f"Main: `{gp['main_story']}` hours \n"
                    f"Main + Extra: `{gp['main_extra']}` hours \n"
                    f"Completionist: `{gp['completionist']}` hours"
                ),
                inline=True,
            )
            embed.add_field(
                name="**Current Completion Progress (Main)**",
                value=f"{gp['progress']:.1f}% \n {self.progress_bar(gp['progress'])}",
                inline=False,
            )
            all_embeds.append(embed)

        for i in range(0, len(all_embeds), 10):
            batch = all_embeds[i : i + 10]
            await ctx.send(embeds=batch)

    def progress_bar(self, completion_progress, number_of_bars=10):
        if number_of_bars < 0:
            return "N/A"
        filled = int(completion_progress * number_of_bars / 100 + 0.5)
        filled = min(filled, number_of_bars)
        return "🟩 " * filled + "⬜ " * (number_of_bars - filled)

async def setup(bot):
    await bot.add_cog(GameProgressBot(bot))



