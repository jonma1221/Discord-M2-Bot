import yt_dlp
import json
import discord
import asyncio

def playYoutubeAudio(voiceClient, URL = ''):
    URL = URL if URL else 'https://www.youtube.com/watch?v=Jdz5uMhu08c'
    # URL = 'https://www.youtube.com/watch?v=Jdz5uMhu08c'

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
        if 'duration' in info: 
            print(f"Duration: {info['duration']} seconds")
        if 'uploader' in info:
            print(f"Uploader: {info['uploader']}")
        print(f"URL: {info['url']}")
        print(f"Format: {info['format']}")
        source = discord.FFmpegPCMAudio(audioUrl) 
        voiceClient.play(source)
    return info

async def fetchYoutubeInfo(URL = ''):
    return await asyncio.get_event_loop().run_in_executor(None, lambda: ytdlp_extract_info(URL))
    

def ytdlp_extract_info(URL):
    URL = URL if URL else 'https://www.youtube.com/watch?v=Jdz5uMhu08c'

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        print(f"Title: {info['title']}")
        if 'duration' in info: 
            print(f"Duration: {info['duration']} seconds")
        if 'uploader' in info:
            print(f"Uploader: {info['uploader']}")
        print(f"URL: {info['url']}")
        print(f"Format: {info['format']}")
    return info