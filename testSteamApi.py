import howlongtobeatpy
from repositories import SteamRepository
from howlongtobeatpy import HowLongToBeat
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def testGetPlayerSummaries():
    steam = SteamRepository()
    summary = await steam.get_player_summaries("76561198005295234")
    print(summary.players[0])
    await steam.close()

async def testRecentlyPlayedGames():
    steam = SteamRepository()
    summary = await steam.get_recently_played_games("76561198047018113")
    print(summary.games)
    await steam.close()

async def testHowLongToBeat():
    howlongtobeatList = await HowLongToBeat().async_search("Divinity: Original Sin 2")
    for game in howlongtobeatList:
        if game is not None:
            print(f"Game: {game.game_name}")
            print(f"Main Completion Time: {game.main_story} hours")

asyncio.run(testRecentlyPlayedGames())



