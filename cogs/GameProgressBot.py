import asyncio
import logging

import discord

from discord.ext import commands
from typing import Any

logger = logging.getLogger(__name__)

from repositories.SteamRepository import SteamRepository
from howlongtobeatpy import HowLongToBeat
from howlongtobeatpy.HowLongToBeatEntry import HowLongToBeatEntry


class GameProgressBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam = SteamRepository()
        self.hltb = HowLongToBeat()

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

        if not self.steam_ids:
            await ctx.reply("No Steam IDs configured yet.")
            return

        game_data, active_ids = await self._fetch_all_recent_games(ctx.guild)

        common_games = self._find_common_games(game_data, active_ids)
        if not common_games:
            await ctx.reply("No common games found.")
            return

        group_progress = await self._lookup_hltb_times(common_games)
        if not group_progress:
            await ctx.reply("No common games with completion data found.")
            return

        embeds = self._build_progress_embeds(group_progress)
        for i in range(0, len(embeds), 10):
            await ctx.send(embeds=embeds[i : i + 10])

    # -- listeners --

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        new_games = self._get_new_game_names(before.activities, after.activities)
        if not new_games:
            return

        steam_id = self.steam_ids.get(after.id)
        if steam_id is None:
            return

        for game_name in new_games:
            await self._notify_game_started(after, game_name, steam_id)

    @staticmethod
    def _get_new_game_names(
        before_activities: tuple[discord.Activity, ...],
        after_activities: tuple[discord.Activity, ...],
    ) -> set[str]:
        before = {
            a.name for a in before_activities
            if a.type == discord.ActivityType.playing
        }
        after = {
            a.name for a in after_activities
            if a.type == discord.ActivityType.playing
        }
        return after - before

    async def _notify_game_started(
        self, member: discord.Member, game_name: str, steam_id: str
    ):
        try:
            response = await self.steam.get_recently_played_games(steam_id)
        except Exception:
            return

        game = next(
            (g for g in response.games if g.name.lower() == game_name.lower()),
            None,
        )
        if game is None:
            return

        hltb_results = await asyncio.to_thread(self.hltb.search, game_name)
        match = self._best_hltb_match(hltb_results) if hltb_results else None

        hours = game.playtime_forever / 60
        if match and match.main_story:
            progress = min((game.playtime_forever / (match.main_story * 60)), 1.0) * 100
            progress_text = f"{self.progress_bar(progress)} {progress:.1f}%"
        else:
            progress_text = "No HLTB data"

        embed = discord.Embed(
            title=f"{member.display_name} started playing {game_name}",
            color=discord.Color.green(),
        )
        if game.icon_url:
            embed.set_thumbnail(url=game.icon_url)
        embed.add_field(name="Playtime", value=f"{hours:.1f} hours", inline=True)
        embed.add_field(name="Completion", value=progress_text, inline=True)

        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(embed=embed)

    # -- data fetching --

    async def _fetch_all_recent_games(
        self, guild: discord.Guild
    ) -> tuple[dict[str, dict[str, Any]], list[int]]:
        game_data: dict[str, dict[str, Any]] = {}
        active_discord_ids: list[int] = []

        for discord_id, steam_id in self.steam_ids.items():
            member = guild.get_member(discord_id)
            if member is None:
                continue

            try:
                response = await self.steam.get_recently_played_games(steam_id)
            except Exception:
                continue

            if not response or not response.games:
                continue

            active_discord_ids.append(discord_id)

            for game in response.games:
                key = game.name.lower()
                if key not in game_data:
                    game_data[key] = {
                        "name": game.name,
                        "icon_url": game.icon_url,
                        "playtimes": {},
                        "members": [],
                    }
                game_data[key]["playtimes"][steam_id] = game.playtime_forever
                if discord_id not in game_data[key]["members"]:
                    game_data[key]["members"].append(discord_id)

        return game_data, active_discord_ids

    # -- common game intersection --

    def _find_common_games(
        self,
        game_data: dict[str, dict[str, Any]],
        active_ids: list[int],
    ) -> list[dict[str, Any]]:
        common = []
        for data in game_data.values():
            has_all = all(did in data["members"] for did in active_ids)
            if not has_all:
                continue

            all_played = all(
                data["playtimes"].get(self.steam_ids[did], 0) > 0
                for did in active_ids
            )
            if not all_played:
                continue

            common.append(data)
        return common

    # -- HLTB lookup --

    @staticmethod
    def _best_hltb_match(
        results: list[HowLongToBeatEntry],
    ) -> HowLongToBeatEntry | None:
        best = None
        for entry in results:
            if entry.main_story is not None and entry.similarity > 0.5:
                if best is None or entry.similarity > best.similarity:
                    best = entry
        return best

    @staticmethod
    def _compute_group_progress(
        playtimes: dict[str, int], main_story_hours: float
    ) -> tuple[float, float]:
        if main_story_hours <= 0:
            return 0.0, 0.0
        min_playtime = min(playtimes.values())
        hours = min_playtime / 60
        main_story_minutes = main_story_hours * 60
        progress = min((min_playtime / main_story_minutes), 1.0) * 100
        return hours, progress

    async def _lookup_hltb_times(
        self, common_games: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        async def search_one(game_info: dict[str, Any]):
            try:
                results = await asyncio.to_thread(
                    self.hltb.search, game_info["name"]
                )
                return game_info, results
            except Exception:
                return game_info, None

        results = await asyncio.gather(*(search_one(g) for g in common_games))

        group = []
        for game_info, hltb_results in results:
            if not hltb_results:
                continue

            match = self._best_hltb_match(hltb_results)
            if match is None or match.main_story == 0:
                continue

            hours, progress = self._compute_group_progress(
                game_info["playtimes"], match.main_story
            )

            group.append({
                "name": game_info["name"],
                "icon_url": game_info["icon_url"],
                "hours": hours,
                "main_story": match.main_story,
                "main_extra": match.main_extra,
                "completionist": match.completionist,
                "progress": progress,
            })

        return group

    # -- embed building --

    def _build_progress_embeds(
        self, group_progress: list[dict[str, Any]]
    ) -> list[discord.Embed]:
        embeds = []
        for gp in group_progress:
            embed = discord.Embed(
                title=gp["name"],
                color=discord.Color.green(),
            )
            if gp["icon_url"]:
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
            embeds.append(embed)
        return embeds

    # -- helpers --

    @staticmethod
    def progress_bar(completion_progress: float, number_of_bars: int = 10) -> str:
        if number_of_bars < 0:
            return "N/A"
        if completion_progress < 0:
            completion_progress = 0.0
        filled = int(completion_progress * number_of_bars / 100 + 0.5)
        filled = max(0, min(filled, number_of_bars))
        return "🟩 " * filled + "⬜ " * (number_of_bars - filled)


async def setup(bot):
    await bot.add_cog(GameProgressBot(bot))
