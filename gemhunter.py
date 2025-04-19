import discord
import logging
from discord.ext import commands
from commands.matrix import MatrixCommand
from commands.react import ReactCommand
from commands.find import FindCommand
from commands.help import HelpCommand
from dotenv import load_dotenv
from keep_alive import keep_alive
import os

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
    bot.tree.add_command(MatrixCommand())
    bot.tree.add_command(ReactCommand())
    bot.tree.add_command(FindCommand())
    bot.tree.add_command(HelpCommand())
    await bot.tree.sync()
    logging.info("✅ Slash commands synced")

keep_alive()
# Inicia o bot
bot.run(discord_token)
