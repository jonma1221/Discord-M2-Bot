import yt_dlp
import json
import discord
import os

# This example requires the 'message_content' intent.
# intents = discord.Intents.default()
# intents.message_content = True
# intents.voice_states = True
# intents.members = True

# client = discord.Client(intents=intents)

def playYoutubeAudio(voiceClient):
    URL = 'https://www.youtube.com/watch?v=Jdz5uMhu08c'

    # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        audioUrl = info['url']
        # ℹ️ ydl.sanitize_info makes the info json-serializable
        # print(json.dumps(ydl.sanitize_info(info)))
        print(f"Title: {info['title']}")
        print(f"Duration: {info['duration']} seconds")
        print(f"Uploader: {info['uploader']}")
        print(f"URL: {info['url']}")
        print(f"Format: {info['format']}")
        source = discord.FFmpegPCMAudio(audioUrl) 
        voiceClient.play(source)

# playYoutubeAudio()