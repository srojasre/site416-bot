import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import typing

# config
BOT_TOKEN = "" # bot token
BLOXLINK_API_KEY = "" # api key must be that server api
GUILD_ID = "1440123598336688140" # discord server id
LOG_CHANNEL_ID = 1440123702707617832 # the threads channel

ALLOWED_ROLE_IDS =[
    111111111111111111,  
    222222222222222222, #the id of the roles allowed to run   
]


async def get_roblox_id(username: str) -> typing.Optional[str]:
    """
    Fetches the Roblox User ID using the provided Roblox username.
    """
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {
        "usernames":[username],
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

class ModerationBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        """
        Executed when the bot is starting up.
        Copies global commands to the specific guild for INSTANT syncing.
        """
        guild = discord.Object(id=int(GUILD_ID))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        
        print(f"Logged in as {self.user} | Slash commands synced instantly to Guild {GUILD_ID}.")

bot = ModerationBot()


@bot.tree.command(name="log", description="Automatically fetches user data and logs a moderation action.")
@app_commands.describe(
    username="The exact Roblox username of the rule-breaker",
    reason="The reason for this punishment",
    punishment="The punishment applied",
    proof="Link to the proof"
)
@app_commands.checks.has_any_role(*ALLOWED_ROLE_IDS) 
async def log_infraction(
    interaction: discord.Interaction, 
    username: str, 
    reason: str, 
    punishment: str, 
    proof: str
):
    """
    Slash command that takes user input, calls the necessary APIs, 
    and posts the formatted log in the designated log channel/forum.
    """
    await interaction.response.defer(ephemeral=True)

    roblox_id = await get_roblox_id(username)
    if not roblox_id:
        await interaction.followup.send(f"Could not find a Roblox account with the username `{username}`.")
        return

    discord_id = await get_discord_id_from_bloxlink(roblox_id)
    discord_username = "Not linked"
    display_discord_id = "Not linked"

    if discord_id:
        display_discord_id = discord_id
        try:
            user_obj = await bot.fetch_user(int(discord_id))
            discord_username = user_obj.name
        except discord.NotFound:
            discord_username = "User left Discord"
        except Exception:
            discord_username = "Error fetching username"

    log_message = (
        f"Roblox Username: `{username}`\n"
        f"Roblox ID: `{roblox_id}`\n"
        f"Discord Username: `{discord_username}`\n"
        f"Discord ID: `{display_discord_id}`\n"
        f"Reason: {reason}\n"
        f"Punishment: {punishment}\n"
        f"Proof: {proof}"
    )

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        await interaction.followup.send("Error: Log channel not found. Please check LOG_CHANNEL_ID in the code.")
        return

    try:
        thread_title = f"{username}"
        
        if isinstance(log_channel, discord.ForumChannel):
            await log_channel.create_thread(name=thread_title, content=log_message)
        else:
            await log_channel.send(log_message)
            
        await interaction.followup.send(f"Log successfully created in <#{LOG_CHANNEL_ID}>.")
        
    except discord.Forbidden:
        await interaction.followup.send("Error: The bot does not have permission to create posts in the channel.")
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {e}")


@log_infraction.error
async def log_infraction_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Handles errors for the log command, specifically missing role permissions.
    """
    if isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message("Error: You do not have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
#TODO Add a bottom for auto-ban and auto warn in the sense of if user is in the discord the moderator has two options
# /ban <userid> 
