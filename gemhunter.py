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

COINGECKO_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"
COINGECKO_COIN_URL = "https://api.coingecko.com/api/v3/coins/{id}"

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

async def fetch_token_stats(network, address):
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            attr = response.json().get("data", {}).get("attributes", {})
            return {
                "price": parse_float(attr.get("price_usd")),
                "fdv": parse_float(attr.get("fdv_usd")),
                "liq": parse_float(attr.get("total_reserve_in_usd")),
                "volume_24h": parse_float(attr.get("volume_usd", {}).get("h24")),
                "desc": attr.get("description"),
                "site": attr.get("websites", [None])[0],
                "name": attr.get("name"),
                "symbol": attr.get("symbol"),
                "gt_score": parse_float(attr.get("gt_score"))
            }
    except Exception as e:
        print(f"❌ Error fetching stats for {address}: {e}")
    return {}

async def fetch_coingecko_coin(symbol: str):
    try:
        all_tokens = requests.get(COINGECKO_LIST_URL).json()
        matched = next((token for token in all_tokens if token["symbol"].lower() == symbol.lower()), None)
        if not matched:
            return None
        coin_data = requests.get(COINGECKO_COIN_URL.format(id=matched["id"])).json()
        return {
            "name": coin_data.get("name"),
            "symbol": coin_data.get("symbol"),
            "desc": coin_data.get("description", {}).get("en", "No description."),
            "site": coin_data.get("links", {}).get("homepage", [None])[0],
            "score": coin_data.get("coingecko_score"),
            "price": coin_data.get("market_data", {}).get("current_price", {}).get("usd"),
            "volume": coin_data.get("market_data", {}).get("total_volume", {}).get("usd"),
            "fdv": coin_data.get("market_data", {}).get("fully_diluted_valuation", {}).get("usd")
        }
    except:
        return None

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
            stats = await fetch_token_stats(net, attr.get("address"))

            name = attr.get("name", "Unnamed")
            symbol = attr.get("symbol", "--")
            net_label = NETWORK_LABELS.get(net, net)

            gt_score = stats.get("gt_score")
            score_emoji = "🧠" if gt_score and gt_score >= 70 else "🧪" if gt_score and gt_score >= 30 else "❌" if gt_score else "❓"
            if stats.get("liq") is not None and stats.get("fdv") is not None:
                risk_emoji = "🔴" if stats["liq"] < 1000 or stats["fdv"] > 10_000_000 else "🟡" if stats["liq"] < 10_000 or stats["fdv"] > 1_000_000 else "🟢"
            else:
                risk_emoji = "❓"

            price = f"${stats['price']:.6f}" if stats.get("price") else "N/A"
            liq_val = f"${stats['liq']:,.0f}" if stats.get("liq") else "N/A"
            fdv_val = f"${stats['fdv']/1_000_000:.1f}M" if stats.get("fdv") else "N/A"
            vol_24h = f"${stats['volume_24h']:,.0f}" if stats.get("volume_24h") else "N/A"

            rows.append(
                f"**{idx}. 💎 {name} ({symbol})** {risk_emoji} {score_emoji} | 🌐 {net_label}\n"
                f"💵 {price} | 💧 {liq_val} | 🧠 {fdv_val}\n"
                f"📊 Volume 24h: {vol_24h}\n"
            )

        legend = (
            "**📘 Legend:**\n"
            "🔴 High Risk | 🟡 Medium | 🟢 Low | ❓ Unknown\n"
            "🧠 Score >70 | 🧪 30–70 | ❌ <30 | ❓ Unknown"
        )

        embed = discord.Embed(title=f"🧠 Gem Matrix — Top 10 Tokens ({network.name})", description="\n".join(rows) + "\n\n" + legend, color=0x00ffcc)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="react", description="Give a fun crypto reaction based on CoinGecko Score")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        try:
            await interaction.response.defer(thinking=True)
        except discord.NotFound:
            print("⚠️ Interaction expired before defer could be sent.")
            return

        stats = await fetch_coingecko_coin(symbol)
        if not stats or stats.get("score") is None:
            await interaction.followup.send(content=f"❌ Token '{symbol.upper()}' not found or has no score.")
            return

        score = stats.get("score")
        if score >= 70:
            msg = f"🧠 {symbol.upper()}? That's a f*cking blue chip, anon! Ape in!"
        elif score >= 30:
            msg = f"🧪 {symbol.upper()}? Meh... mid-tier stuff. Might moon, might rug."
        else:
            msg = f"❌ {symbol.upper()}? Bro that's absolute sh*t. Get out before it rugs."
        await interaction.followup.send(content=msg)

    @app_commands.command(name="find", description="Do a deep dive on a specific token")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        try:
            await interaction.response.defer(thinking=True)
        except discord.NotFound:
            print("⚠️ Interaction expired before defer could be sent.")
            return

        stats = await fetch_coingecko_coin(symbol)
        if not stats:
            await interaction.followup.send(content=f"❌ Token '{symbol.upper()}' not found.")
            return

        emoji = "🧠" if stats["score"] and stats["score"] > 70 else "🧪" if stats["score"] and stats["score"] > 30 else "❌"
        score_str = f"{emoji} {stats['score']:.2f}" if stats["score"] else "❓ Unknown"
        embed = discord.Embed(title=f"🔎 Deep Dive — {stats['name']} ({stats['symbol'].upper()})", color=0x0099ff)
        embed.add_field(name="GT Score", value=score_str, inline=True)
        embed.add_field(name="Website", value=stats.get("site", "N/A"), inline=False)
        embed.add_field(name="Description", value=stats.get("desc", "No description found.")[:1024], inline=False)
        embed.add_field(name="💵 Price", value=f"${stats['price']:.6f}" if stats["price"] else "N/A", inline=True)
        embed.add_field(name="🧠 FDV", value=f"${stats['fdv'] / 1_000_000:.1f}M" if stats["fdv"] else "N/A", inline=True)
        embed.add_field(name="📊 Volume", value=f"${stats['volume']:,.0f}" if stats["volume"] else "N/A", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="Show all GemHunter commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Welcome to GemHunter!", color=0x00ffcc)
        embed.add_field(name="/gemhunter matrix", value="GemMatrix - List the 10 newest tokens with optional network filter.", inline=False)
        embed.add_field(name="/gemhunter react <symbol>", value="React - Give a funny crypto reaction based on CoinGecko Score.", inline=False)
        embed.add_field(name="/gemhunter find <symbol>", value="Find - Analyze a specific token in depth.", inline=False)
        await interaction.response.send_message(embed=embed)

bot.tree.add_command(GemHunter())

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")
    for guild in bot.guilds:
        try:
            await bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"✅ Synced updated commands to: {guild.name} ({guild.id})")
        except Exception as e:
            print(f"❌ Sync failed for {guild.name}: {e}")

bot.run(discord_gem_hunter)
