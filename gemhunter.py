import logging
import os
from discord.ext import commands
from dotenv import load_dotenv
import discord
from commands.find import FindCommand
from commands.group import GemHunterGroup
from commands.help import HelpCommand
from commands.matrix import MatrixCommand
from commands.react import ReactCommand
from keep_alive import keep_alive

# Carrega variáveis de ambiente
keep_alive()
load_dotenv()
discord_token = os.getenv("DISCORD_BOT")

# Setup de logs
logging.basicConfig(level=logging.INFO)

# Configura o bot com intents básicos
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Evento ao iniciar
@bot.event
async def on_ready():
    logging.info(f"🟢 Logged in as {bot.user}")
    bot.tree.add_command(GemHunterGroup())
    await bot.tree.sync()
    logging.info("✅ Slash commands synced")

keep_alive()
# Inicia o bot
bot.run(discord_token)
