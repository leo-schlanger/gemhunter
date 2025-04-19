from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import discord

from keep_alive import keep_alive
from commands.matrix import MatrixCommand
from commands.find import FindCommand
from commands.react import ReactCommand
from commands.help import HelpCommand

load_dotenv()
keep_alive()

discord_gem_hunter = os.getenv("DISCORD_BOT")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

class GemHunter(app_commands.Group):
    def __init__(self):
        super().__init__(name="gemhunter", description="The ultimate gem analyzer")
        self.add_command(MatrixCommand())
        self.add_command(ReactCommand())
        self.add_command(FindCommand())
        self.add_command(HelpCommand())

bot.tree.add_command(GemHunter())

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")
    await bot.tree.sync()

bot.run(discord_gem_hunter)
