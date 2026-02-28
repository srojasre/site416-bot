# utils/api_helpers.py
import aiohttp
import typing
from config import GUILD_ID, BLOXLINK_API_KEY

async def get_roblox_id(username: str) -> typing.Optional[str]:
    """
    Fetches the Roblox User ID using the provided Roblox username.
    """
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {
        "usernames": [username],
        "excludeBannedUsers": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        return str(data["data"][0]["id"])
        except Exception as e:
            print(f"[Error] Failed to fetch Roblox ID: {e}")
            
    return None

async def get_discord_id_from_bloxlink(roblox_id: str) -> typing.Optional[str]:
    """
    Fetches the Discord User ID from the Bloxlink API using a Roblox ID.
    """
    url = f"https://api.blox.link/v4/public/guilds/{GUILD_ID}/roblox-to-discord/{roblox_id}"
    headers = {
        "Authorization": BLOXLINK_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("discordIDs") and len(data["discordIDs"]) > 0:
                        return str(data["discordIDs"][0])
        except Exception as e:
            print(f"[Error] Failed to fetch Discord ID from Bloxlink: {e}")
            
    return None