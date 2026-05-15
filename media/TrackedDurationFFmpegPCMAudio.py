import discord

class TrackedDurationFFmpegPCMAudio(discord.PCMVolumeTransformer):
    def __init__(self, original, seekedTime=0):
        super().__init__(original)
        self.currentTime = 0
        self.seekedTime = seekedTime

    # def __init__(self, urlSource, *, before_options, options):
    #     self.urlSource = urlSource
    #     self.before_options = before_options
    #     self.currentTime = 0
    #     super().__init__(urlSource, before_options=before_options, options=options)
    
    def read(self) -> bytes:
        self.currentTime += 20
        return super().read()
    
    def checkTimestampInSec(self):
        return self.currentTime / 1000 + self.seekedTime