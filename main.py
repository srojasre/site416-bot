import discord
from discord.ext import commands
from config import GUILD_ID, BOT_TOKEN

class ModerationBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        """
        Executed when the bot is starting up.
        """
        await self.load_extension("cogs.moderation") 
        guild = discord.Object(id=int(GUILD_ID))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        
        print(f"Logged in as {self.user} | Slash commands synced instantly to Guild {GUILD_ID}.")

def main():
    bot = ModerationBot()
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()