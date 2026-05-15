import discord
import utils.MediaUtil
class MediaControlsContainer(discord.ui.LayoutView):
    def __init__(
        self, 
        *, 
        voice_client, 
        video_title, 
        video_thumbnail, 
        video_duration, 
        video_volume,
        timeout=1800):

        super().__init__(timeout=timeout)
        self.voice_client = voice_client
        self.title = discord.ui.TextDisplay(video_title)
        self.separator = discord.ui.Separator()
        self.videoVolume = discord.ui.TextDisplay(f"``Volume:`` {video_volume}")
        if video_duration:
            minutes, seconds = utils.MediaUtil.convertSecondsToMinutesAndSeconds(video_duration)
            self.duration = discord.ui.TextDisplay(f"``Duration:`` {minutes}m {seconds}s")
            self.section = discord.ui.Section(
                self.title,
                self.duration,
                self.videoVolume,
                accessory=discord.ui.Thumbnail(media=video_thumbnail)
            )
        else:
            self.section = discord.ui.Section(
                self.title, 
                self.videoVolume,
                accessory=discord.ui.Thumbnail(media=video_thumbnail))
        self.actionRow = MediaControlsActionRow(self, voice_client)

        container = discord.ui.Container(
            self.section, 
            self.separator, 
            self.actionRow, 
            accent_color=discord.Color.greyple())
        self.add_item(container)
        # self.add_item(self.section)
        # self.add_item(self.actionRow)

class MediaControlsActionRow(discord.ui.ActionRow):
    def __init__(self, parentView: 'MediaControlsContainer', voice_client):
        super().__init__()
        self.parentView = parentView
        self.voice_client = voice_client
    
    @discord.ui.button(label="Pause",style=discord.ButtonStyle.green, emoji="⏯️")
    async def playButton(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"interaction ${interaction}")
        print(f"interaction client ${interaction.client}")
        print(f"Button label - {button.label}")
        print(f"self - {self}")
        print(f"self.parentView - {self.parentView}")
        print(f"voice_client ${self.voice_client} | is_playing:{self.voice_client.is_playing()} | is_paused:{self.voice_client.is_paused()}")
        if self.voice_client.is_playing():
            print(f"voice_client changed from playing to paused")
            button.label = "Resume"
            print(f"Button label - {button.label}")
            await interaction.response.edit_message(
                view=self.parentView
            )
            self.voice_client.pause()
        elif self.voice_client.is_paused():
            print(f"voice_client changed from paused to resume")
            button.label = "Pause"
            print(f"Button label - {button.label}")
            await interaction.response.edit_message(
                view=self.parentView
            )
            self.voice_client.resume()
        
    @discord.ui.button(label="Stop",style=discord.ButtonStyle.red, emoji="⏹️")
    async def stopButton(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"Button label - {button.label}")
        # await interaction.response.edit_message(view=self.parentView)
        self.voice_client.stop()
        await interaction.message.delete()
        await self.voice_client.disconnect()
    
    @discord.ui.button(label="Increase Volume",style=discord.ButtonStyle.grey, emoji="🔊")
    async def increaseVolume(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"Button label - {button.label}")
        print(f"Current Volume: {self.voice_client.source.volume}")
        if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
            newVolume = min(float(self.voice_client.source.volume) + 0.1, 1.0)
            self.voice_client.source.volume = newVolume
            self.parentView.videoVolume.content = f"``Volume:`` {newVolume * 100}%"
            print(f"Volume: {newVolume}")
            await interaction.response.edit_message(view=self.parentView)

    @discord.ui.button(label="Decrease Volume",style=discord.ButtonStyle.grey, emoji="🔉")
    async def decreaseVolume(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"Button label - {button.label}")
        print(f"Current Volume: {self.voice_client.source.volume}")
        if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
            newVolume = float(self.voice_client.source.volume) - 0.1 if float(self.voice_client.source.volume) - 0.1 > 0 else 0
            self.voice_client.source.volume = newVolume
            self.parentView.videoVolume.content = f"``Volume:`` {newVolume * 100}%"
            print(f"Volume: {newVolume}")
            await interaction.response.edit_message(view=self.parentView)