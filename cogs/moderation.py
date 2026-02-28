# cogs/moderation.py
import discord
from discord.ext import commands
from discord import app_commands

from config import LOG_CHANNEL_ID, ALLOWED_ROLE_IDS
from utils.api_helpers import get_roblox_id, get_discord_id_from_bloxlink
#professional way of doing this totally not ASKED CHAT GPT HOW TO DO IT LIKE THIS
class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="log", description="Automatically fetches user data and logs a moderation action.")
    @app_commands.describe(
        username="The exact Roblox username of the rule-breaker",
        reason="The reason for this punishment",
        punishment="The punishment applied",
        proof="Link to the proof"
    )
    @app_commands.checks.has_any_role(*ALLOWED_ROLE_IDS) 
    async def log_infraction(
        self, 
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
                # Nota: usando self.bot en lugar de bot
                user_obj = await self.bot.fetch_user(int(discord_id))
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

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
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
    async def log_infraction_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Handles errors for the log command, specifically missing role permissions.
        """
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message("Error: You do not have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))