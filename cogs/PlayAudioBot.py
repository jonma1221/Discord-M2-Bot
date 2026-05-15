import discord
import media.MediaControlsContainer
import media.TrackedDurationFFmpegPCMAudio
import utils.MediaUtil
import time

from yt_dl_helper import (
    fetchYoutubeInfo
)
from discord.ext import commands

class PlayAudioBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="play", description="Play Audio", brief="Provide a youtube link for the audio source")
    async def playAudio(self, ctx, link):
        await ctx.defer()
        # Get the voice channel by ID
        if not ctx.author.voice:
            return await ctx.reply("You must be connected to a voice channel", ephemeral=True) 
        print(f"Command ctx.author.voice.channel: {ctx.author.voice.channel} | channel id: {ctx.author.voice.channel.id}")

        # Check if bot is already connected to the same voice channel of the user running the command
        if self.bot.voice_clients:
            for client in self.bot.voice_clients:
                if client.channel.id:
                    voice_client = client
                    print(f"Already connected to client {voice_client}")
        else:
            voice_client = await ctx.author.voice.channel.connect()
            print(f"""
            Connected to voice channel: {voice_client}
            User: {voice_client.user}
            """)

        self.audioInfo = await fetchYoutubeInfo(link)

        if voice_client.is_playing():
            await ctx.reply("Already playing audio", ephemeral=True)
            return 
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        source = discord.FFmpegPCMAudio(self.audioInfo['url'], **ffmpeg_options) 
        # source = media.TrackedDurationFFmpegPCMAudio.TrackedDurationFFmpegPCMAudio(info['url'], **ffmpeg_options) 
        source = media.TrackedDurationFFmpegPCMAudio.TrackedDurationFFmpegPCMAudio(source, 0)
        # source = discord.PCMVolumeTransformer(source)
        source.volume = 0.1
        voice_client.play(source)
        self.currentAudio = await ctx.reply(view=media.MediaControlsContainer.MediaControlsContainer(
                voice_client = voice_client, 
                video_title = f"### Now playing: **{self.audioInfo['title']}**",
                video_thumbnail = self.audioInfo['thumbnail'],
                video_duration = self.audioInfo['duration'] if 'duration' in self.audioInfo else None,
                video_volume = f"{source.volume * 100}%"
            )
        )
        print(f"Current Audio - {self.currentAudio}")

    @commands.hybrid_command(name="volume", description="Adjust Volume", brief="Provide a number between 1 and 100")
    async def adjustVolume(self, ctx, volume):
        await ctx.defer()
        if ctx.voice_client is None:
            await ctx.send("Not connected to a voice channel.")
        try:
            # Attempt conversion
            new_volume = float(volume)
            ctx.voice_client.source.volume = new_volume
            await ctx.reply(f"Volume adjusted to {new_volume}", ephemeral=True)
        except ValueError:
            # This triggers if the string isn't a valid float or int
            await ctx.send(f"'{volume}' is not a valid number.")
        print(f"new_volume - {new_volume}")
        print(f"adjustVolume bot - {self.bot}")
        print(f"adjustVolume ctx voice_client - {ctx.voice_client}")
        print(f"adjustVolume ctx voice_client source - {ctx.voice_client.source}")
        print(f"adjustVolume ctx voice_client source volume - {ctx.voice_client.source.volume}")

    @commands.hybrid_command(name="skip", description="Skip ahead in the audio", brief="Provide a number to fast forward in the audio")
    async def seekForward(self, ctx, forwarded_amount):
        await ctx.defer()
        print(f"forwarded_amount - {forwarded_amount}")
        currentTimeStamp = ctx.voice_client.source.checkTimestampInSec()
        minutes, seconds = utils.MediaUtil.convertSecondsToMinutesAndSeconds(currentTimeStamp)
        print(f"Current timestamp - {minutes}m {seconds}s")

        # 1. Get current position and add the forwarded amount
        new_timestamp = currentTimeStamp + float(forwarded_amount)
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

        ffmpeg_options = {
            'before_options': f'-ss {forwarded_amount} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': f'-vn'
        }
        source = discord.FFmpegPCMAudio(self.audioInfo['url'], **ffmpeg_options) 
        source = media.TrackedDurationFFmpegPCMAudio.TrackedDurationFFmpegPCMAudio(source)
        source.volume = 0.1
        ctx.voice_client.play(source)
        print(f"Fast Forwarded Audio Playing - {ctx.voice_client.is_playing()}")
        await ctx.send(f"Current timestamp - {minutes}m {seconds}s")

async def setup(bot):
    await bot.add_cog(PlayAudioBot(bot)) 