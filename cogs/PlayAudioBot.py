import asyncio
import discord
import media.MediaControls

from yt_dl_helper import (
    playYoutubeAudio,
    fetchYoutubeInfo
)
from discord.ext import commands

class PlayAudioBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="play", description="Play Audio", brief="Provide a youtube link for the audio source")
    async def playAudio(self, ctx, link):
        # Get the voice channel by ID
        channel = self.bot.get_channel(1494790482763583591)
        print(f"Get channel details: {channel}")
        voice_client = await channel.connect()
        print(f"""
        Connected to voice channel: {voice_client}
        User: {voice_client.user}
        """)
        await ctx.defer()
        # playYoutubeAudio(voice_client, link)
        info = await fetchYoutubeInfo(link)

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        source = discord.FFmpegPCMAudio(info['url'], **ffmpeg_options) 
        source = discord.PCMVolumeTransformer(source)
        source.volume = 0.1
        voice_client.play(source)
        await ctx.reply(f"Now playing: **{info['title']}**", view=media.MediaControls.MediaControls(voice_client=voice_client))
        

async def setup(bot):
    await bot.add_cog(PlayAudioBot(bot)) 