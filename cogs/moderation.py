import discord
from discord.ext import commands
from discord import app_commands

from config import LOG_CHANNEL_ID, ALLOWED_ROLE_IDS, COMMAND_CHANNEL_ID, ADMIN_LOG_CHANNEL_ID
from utils.api_helpers import get_roblox_id, get_discord_id_from_bloxlink

class DynoActionModal(discord.ui.Modal):
    """A modal popup that prompts the moderator for a reason before executing a Dyno command."""
    def __init__(self, action: str, discord_id: str):
        super().__init__(title=f"Execute {action.capitalize()} via Dyno")
        self.action = action # "warn" or "ban"
        self.discord_id = discord_id

        self.reason_input = discord.ui.TextInput(
            label="Reason for punishment",
            style=discord.TextStyle.paragraph,
            placeholder=f"Enter the reason for the {action} here...",
            required=True,
            max_length=300
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        command_str = f"?{self.action} {self.discord_id} {self.reason_input.value}"
        await interaction.channel.send(command_str)
        
        await interaction.response.send_message(
            f"**Command successfully dispatched to the channel:**\n`{command_str}`\n\n"
            f"*(Note: If Dyno fails to respond automatically, please copy and manually paste the command above.)*",
            ephemeral=True
        )

class ActionButtons(discord.ui.View):
    """Interactive buttons attached to the moderation log."""
    def __init__(self, discord_id: str):
        super().__init__(timeout=None) 
        self.discord_id = discord_id

    @discord.ui.button(label="Warn (Dyno)", style=discord.ButtonStyle.primary, custom_id="btn_warn")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DynoActionModal("warn", self.discord_id))

    @discord.ui.button(label="Ban (Dyno)", style=discord.ButtonStyle.danger, custom_id="btn_ban")
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DynoActionModal("ban", self.discord_id))

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="log", description="Logs an infraction and provides auto-moderation tools.")
    @app_commands.describe(
        username="The exact Roblox username of the offender",
        reason="The reason for the punishment",
        punishment="The specific punishment applied",
        proof="URL linking to the evidence",
        platform="The platform where the infraction occurred",
        punishment_type="The general category of the punishment"
    )
    @app_commands.choices(
        platform=[
            app_commands.Choice(name="Discord", value="Discord"),
            app_commands.Choice(name="In-game", value="In-game"),
            app_commands.Choice(name="Both", value="Both")
        ],
        punishment_type=[
            app_commands.Choice(name="Warning", value="Warning"),
            app_commands.Choice(name="Ban", value="Ban"),
            app_commands.Choice(name="Blacklist", value="Blacklist")
        ]
    )
    @app_commands.checks.has_any_role(*ALLOWED_ROLE_IDS) 
    async def log_infraction(
        self, 
        interaction: discord.Interaction, 
        username: str, 
        reason: str, 
        punishment: str, 
        proof: str,
        platform: app_commands.Choice[str],
        punishment_type: app_commands.Choice[str]
    ):
       
        if interaction.channel_id != int(COMMAND_CHANNEL_ID):
            await interaction.response.send_message(
                f"Permission Denied: This command can only be executed in <#{COMMAND_CHANNEL_ID}>.", 
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False) 

        roblox_id = await get_roblox_id(username)
        if not roblox_id:
            await interaction.followup.send(f"Error: Could not locate a Roblox account associated with the username `{username}`.")
            return

        discord_id = await get_discord_id_from_bloxlink(roblox_id)
        discord_username = "Not linked"
        display_discord_id = "Not linked"

        if discord_id:
            display_discord_id = discord_id
            try:
                user_obj = await self.bot.fetch_user(int(discord_id))
                discord_username = user_obj.name
            except Exception:
                discord_username = "Error fetching user data"

        log_message = (
            f"**Roblox Username:** `{username}`\n"
            f"**Roblox ID:** `{roblox_id}`\n"
            f"**Discord Username:** `{discord_username}`\n"
            f"**Discord ID:** `{display_discord_id}`\n"
            f"**Type:** {punishment_type.value} | **Platform:** {platform.value}\n"
            f"**Reason:** {reason}\n"
            f"**Punishment:** {punishment}\n"
            f"**Proof:** {proof}"
        )

        log_channel = self.bot.get_channel(int(LOG_CHANNEL_ID))
        if not log_channel:
            await interaction.followup.send("System Error: The designated logging channel could not be found.")
            return

       
        applied_tags =[]
        if isinstance(log_channel, discord.ForumChannel):
            tag_names_to_find = [punishment_type.value]
            
            if platform.value == "Both":
                tag_names_to_find.extend(["Discord", "In-game"])
            else:
                tag_names_to_find.append(platform.value)
            
            
            for tag in log_channel.available_tags:
                if tag.name in tag_names_to_find:
                    applied_tags.append(tag)

        try:
            thread_title = f"{username}"
            
            if isinstance(log_channel, discord.ForumChannel):
                await log_channel.create_thread(name=thread_title, content=log_message, applied_tags=applied_tags)
            else:
                await log_channel.send(f"**{thread_title}**\n{log_message}")
                
           
            admin_channel = self.bot.get_channel(int(ADMIN_LOG_CHANNEL_ID))
            if admin_channel:
                admin_msg = (
                    f"**New Moderation Log Entry**\n"
                    f"**Moderator:** {interaction.user.mention}\n"
                    f"**Offender:** `{username}`\n"
                    f"**Category:** {punishment_type.value} | **Platform:** {platform.value}\n"
                    f"**Reference:** <#{LOG_CHANNEL_ID}>"
                )
                await admin_channel.send(admin_msg)

           
            view = ActionButtons(discord_id) if discord_id else discord.utils.MISSING
            
            response_msg = f"Success: Log created in <#{LOG_CHANNEL_ID}>.\n\n**Details:**\n{log_message}"
            if not discord_id:
                response_msg += "\n\n*Note: The user does not have a linked Discord account. Auto-moderation functionalities are disabled for this entry.*"

            await interaction.followup.send(response_msg, view=view)
            
        except discord.Forbidden:
            await interaction.followup.send("Error: The bot lacks the necessary permissions to perform this action.")
        except Exception as e:
            await interaction.followup.send(f"An unexpected system error occurred: {e}")

    @log_infraction.error
    async def log_infraction_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message("Permission Denied: You do not possess the required clearance to execute this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An internal error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))