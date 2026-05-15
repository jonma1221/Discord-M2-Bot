import discord
from discord.ext import commands

class MediaControls(discord.ui.View):
    def __init__(self, *, voice_client, timeout=1800):
        super().__init__(timeout=timeout)
        self.voice_client = voice_client

    @discord.ui.button(label="Pause",style=discord.ButtonStyle.green, emoji="⏯️")
    async def playButton(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"interaction ${interaction}")
        print(f"interaction client ${interaction.client}")
        print(f"Button label - {button.label}")
        print(f"voice_client ${self.voice_client} | is_playing:{self.voice_client.is_playing()} | is_paused:{self.voice_client.is_paused()}")
        if self.voice_client.is_playing():
            print(f"voice_client changed from playing to paused")
            button.label = "Resume"
            print(f"Button label - {button.label}")
            await interaction.response.edit_message(view=self)
            self.voice_client.pause()
        elif self.voice_client.is_paused():
            print(f"voice_client changed from paused to resume")
            button.label = "Pause"
            print(f"Button label - {button.label}")
            await interaction.response.edit_message(view=self)
            self.voice_client.resume()
        
    @discord.ui.button(label="Stop",style=discord.ButtonStyle.red, emoji="⏹️")
    async def stopButton(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(f"Button clicked ${button}")
        print(f"Button label - {button.label}")
        await interaction.response.edit_message(view=self)
        self.voice_client.stop()
        await self.voice_client.disconnect()
    
    @discord.ui.select(
        placeholder="Volume",
        options=[
            discord.SelectOption(label="1", value="1"),
            discord.SelectOption(label="2", value="2"),
            discord.SelectOption(label="3", value="3"),
            discord.SelectOption(label="4", value="4"),
            discord.SelectOption(label="5", value="5"),
            discord.SelectOption(label="50", value="50"),
            discord.SelectOption(label="100", value="100"),
        ]
    )
    async def select_callback(self, interaction, select):
        print(f"Selected - {select}")
        newVolume = float(select.values[0]) / 100
        if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
            self.voice_client.source.volume = newVolume
            self.placeholder=f"Volume: {newVolume}%"
            await interaction.response.edit_message(view=self)
        # await interaction.response.send_message(f"You selected: {select.values[0]}")