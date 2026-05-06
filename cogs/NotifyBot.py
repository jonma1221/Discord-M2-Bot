import asyncio
import discord

from discord.ext import commands
from typing import Optional

class NotifyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connectedGuilds = bot.connectedGuilds
        self.discordUserHelper = bot.discordUserHelper

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ):
        discriminator = getattr(member, "discriminator", "0")
        tag = member.name if discriminator in (None, "0") else f"{member.name}#{discriminator}"
        global_name = getattr(member, "global_name", None)
        roles_count = len(getattr(member, "roles", []) or [])

        def _is_voice_channel(channel: Optional[discord.abc.GuildChannel]) -> bool:
            """True for normal voice channels only (not stage)."""
            return isinstance(channel, discord.VoiceChannel)

        # Joined a voice channel: was not connected to guild voice before, now in a VoiceChannel.
        # (Mute/deafen/self-stream updates keep the same channel and won't match this.)
        if (
            not member.bot
            and before.channel is None
            and after.channel is not None
            and _is_voice_channel(after.channel)
        ):
            # Update cached voice_channel_id for this member.
            # cached = guild_member_data.get(after.channel.guild.id)
            # if cached and isinstance(cached.get("member_index"), dict):
            #     entry = cached["member_index"].get(member.id)
            #     if isinstance(entry, dict):
            #         entry["voice_channel_id"] = after.channel.id

            print(
                f"{tag} ({member.display_name}{' / ' + global_name if global_name else ''}) "
                f"joined voice: {after.channel.name} "
                f"(user_id={member.id}, bot={member.bot}, roles={roles_count}, "
                f"guild={after.channel.guild.name}, channel_id={after.channel.id})"
            )
            asyncio.create_task(
                self._scan_guild_and_nudge(after.channel.guild, skip_user_id=member.id)
            )
            return

        # Moved between voice channels (still a "join" of the new channel)
        if (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            print(
                f"{tag} ({member.display_name}{' / ' + global_name if global_name else ''}) "
                f"moved voice: {before.channel.name} -> {after.channel.name} "
                f"(user_id={member.id}, bot={member.bot}, roles={roles_count}, guild={after.channel.guild.name})"
            )

    async def _scan_guild_and_nudge(self, guild: discord.Guild, *, skip_user_id: int) -> None:
        try:
            print(f"Connected guilds {self.connectedGuilds}")
            # cached = self.connectedGuilds.get(guild.id)
            # if not cached:
            #     print(f"No cached guild_member_data for guild_id={guild.id}; skipping nudge scan.")
            #     return

            # members = cached.get("members", [])
            members = guild.members
            nudged = 0

            for member in members:
                user_id = member.id
                # if user_id == skip_user_id:
                #     continue

                voice_channel = getattr(member, "voice", None)
                print(f"[NotifyBot] Checking {member}")
                if voice_channel is None and not member.bot:
                    dm_sent = await self.discordUserHelper.dm_user(user_id, "Hop on, it's time to start!")
                    if dm_sent:
                        nudged += 1
                        print(f"DM sent to {member.name}")

            print(f"Nudge scan complete for guild {guild.id}. DMs sent: {nudged}")
        except Exception as e:
            print(f"Nudge scan crashed for guild {guild.id}: {e!r}")

async def setup(bot):
    await bot.add_cog(NotifyBot(bot))