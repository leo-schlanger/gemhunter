import discord
from discord.ext import commands
from discord import app_commands
import requests
import os
import asyncio
from keep_alive import keep_alive
from dotenv import load_dotenv

keep_alive()
load_dotenv()

discord_gem_hunter = os.getenv("DISCORD_BOT")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

NETWORK_LABELS = {
    "eth": "Ethereum", "bsc": "BNB Chain", "polygon": "Polygon", "solana": "Solana",
    "base": "Base", "arbitrum": "Arbitrum", "optimism": "Optimism", "avax": "Avalanche",
    "fantom": "Fantom", "unknown": "Unknown"
}

NETWORK_CHOICES = [
    app_commands.Choice(name="ethereum", value="eth"),
    app_commands.Choice(name="bsc", value="bsc"),
    app_commands.Choice(name="polygon", value="polygon"),
    app_commands.Choice(name="solana", value="solana"),
    app_commands.Choice(name="base", value="base"),
    app_commands.Choice(name="arbitrum", value="arbitrum"),
    app_commands.Choice(name="optimism", value="optimism"),
    app_commands.Choice(name="avax", value="avax"),
    app_commands.Choice(name="fantom", value="fantom"),
    app_commands.Choice(name="all", value="all")
]

class GemHunter(app_commands.Group):
    def __init__(self):
        super().__init__(name="gemhunter", description="The ultimate gem analyzer")

    @app_commands.command(name="matrix", description="List the 10 newest tokens with GT score and risk")
    @app_commands.describe(network="Filter by blockchain network (or use all)")
    @app_commands.choices(network=NETWORK_CHOICES)
    async def matrix(self, interaction: discord.Interaction, network: app_commands.Choice[str]):
        await interaction.response.defer(thinking=True)
        tokens = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated").json().get("data", [])
        filtered = [t for t in tokens if network.value == "all" or t.get("relationships", {}).get("network", {}).get("data", {}).get("id") == network.value][:10]

        rows = []
        for idx, token in enumerate(filtered, 1):
            attr = token["attributes"]
            net = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")

            name = attr.get("name", "Unnamed")
            symbol = attr.get("symbol", "--")
            net_label = NETWORK_LABELS.get(net, net)

            price = attr.get("price_usd", "N/A")
            gt_score = attr.get("gt_score")
            liq = attr.get("total_reserve_in_usd")
            fdv = attr.get("fdv_usd")
            volume = attr.get("volume_usd", {}).get("h24")

            score_emoji = "🧠" if gt_score and gt_score >= 70 else "🧪" if gt_score and gt_score >= 30 else "❌" if gt_score else "❓"
            risk_emoji = "🔴" if liq and float(liq) < 1000 or fdv and float(fdv) > 10_000_000 else "🟡" if liq and float(liq) < 10_000 or fdv and float(fdv) > 1_000_000 else "🟢"

            rows.append(
                f"**{idx}. 💎 {name} ({symbol})** {risk_emoji} {score_emoji} | 🌐 {net_label}\n"
                f"💵 {price} | 💧 {liq or 'N/A'} | 🧠 {fdv or 'N/A'}\n"
                f"📊 Volume 24h: {volume or 'N/A'}\n"
            )

        legend = (
            "**📘 Legend:**\n"
            "🔴 High Risk | 🟡 Medium | 🟢 Low | ❓ Unknown\n"
            "🧠 Score >70 | 🧪 30–70 | ❌ <30 | ❓ Unknown"
        )

        embed = discord.Embed(title=f"🧠 Gem Matrix — Top 10 Tokens ({network.name})", description="\n".join(rows) + "\n\n" + legend, color=0x00ffcc)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="react", description="Give a fun crypto reaction based on CoinGecko sentiment")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(thinking=True)
        token_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        match = next((t for t in token_list if t['symbol'].lower() == symbol.lower()), None)
        if not match:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return
        token_data = requests.get(f"https://api.coingecko.com/api/v3/coins/{match['id']}").json()
        sentiment = token_data.get("sentiment_votes_up_percentage", 0)

        if sentiment >= 70:
            msg = f"🧠 {symbol.upper()}? That's a f*cking blue chip, anon! Ape in!"
        elif sentiment >= 30:
            msg = f"🧪 {symbol.upper()}? Mid-tier vibes... might moon, might rug."
        else:
            msg = f"❌ {symbol.upper()}? Total trash. Stay away."

        await interaction.followup.send(content=msg)

    @app_commands.command(name="find", description="Do a deep dive on a specific token")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(thinking=True)
        token_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        match = next((t for t in token_list if t['symbol'].lower() == symbol.lower()), None)
        if not match:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return
        token_data = requests.get(f"https://api.coingecko.com/api/v3/coins/{match['id']}").json()

        name = token_data.get("name", "Unknown")
        desc = token_data.get("description", {}).get("en", "No description.")
        homepage = token_data.get("links", {}).get("homepage", [None])[0]
        sentiment = token_data.get("sentiment_votes_up_percentage")
        emoji = "🧠" if sentiment and sentiment >= 70 else "🧪" if sentiment and sentiment >= 30 else "❌"
        score_str = f"{emoji} {sentiment:.2f}%" if sentiment else "❓ Unknown"

        embed = discord.Embed(title=f"🔎 Deep Dive — {name} ({symbol.upper()})", color=0x0099ff)
        embed.add_field(name="Sentiment", value=score_str, inline=True)
        embed.add_field(name="Website", value=homepage or "N/A", inline=False)
        embed.add_field(name="Description", value=desc[:1000], inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="Show all GemHunter commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Welcome to GemHunter!", color=0x00ffcc)
        embed.add_field(name="/gemhunter matrix", value="List 10 newest tokens with filters", inline=False)
        embed.add_field(name="/gemhunter react <symbol>", value="Crypto reaction with sentiment 💩 or 🔥", inline=False)
        embed.add_field(name="/gemhunter find <symbol>", value="Deep analysis of token with sentiment and info", inline=False)
        await interaction.response.send_message(embed=embed)

bot.tree.add_command(GemHunter())

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")
    await bot.tree.sync()
bot.run(discord_gem_hunter)
