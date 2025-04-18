import discord
from discord.ext import commands
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
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print("🟢 GemHunter is online!")

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
            }
    except Exception as e:
        print(f"❌ Error fetching token stats: {e}")
    return {}

# Nome amigável das redes
NETWORK_LABELS = {
    "eth": "Ethereum",
    "bsc": "BNB Chain",
    "polygon": "Polygon",
    "solana": "Solana",
    "base": "Base",
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "avax": "Avalanche",
    "fantom": "Fantom",
    "unknown": "Unknown",
}

@bot.command()
async def gemhunter(ctx):
    await ctx.send("🔍 Scanning newest token gems...")

    base_url = "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated"
    response = requests.get(base_url)

    if response.status_code != 200:
        await ctx.send("❌ Failed to fetch token list.")
        return

    tokens = response.json().get("data", [])[:10]

    rows = []
    for idx, token in enumerate(tokens, 1):
        attr = token["attributes"]
        relationships = token.get("relationships", {})

        name = attr.get("name", "Unnamed")
        symbol = attr.get("symbol", "--")
        address = attr.get("address")
        gt_score = parse_float(attr.get("gt_score"))
        network_key = relationships.get("network", {}).get("data", {}).get("id", "unknown")
        network_name = NETWORK_LABELS.get(network_key, network_key.capitalize())

        stats = await fetch_token_stats(network_key, address)

        # Score emoji
        if gt_score is not None:
            if gt_score >= 70:
                score_emoji = "🧠"
            elif gt_score >= 30:
                score_emoji = "🧪"
            else:
                score_emoji = "❌"
        else:
            score_emoji = "❓"

        # Risco emoji
        if stats.get("liq") is not None and stats.get("fdv") is not None:
            liq = stats["liq"]
            fdv = stats["fdv"]
            if liq < 1000 or fdv > 10_000_000:
                risk_emoji = "🔴"
            elif liq < 10_000 or fdv > 1_000_000:
                risk_emoji = "🟡"
            else:
                risk_emoji = "🟢"
        else:
            risk_emoji = "❓"

        # Valores
        price = f"${stats['price']:.6f}" if stats.get("price") else "N/A"
        liq_val = f"${stats['liq']:,.0f}" if stats.get("liq") else "N/A"
        fdv_val = f"${stats['fdv']/1_000_000:.1f}M" if stats.get("fdv") else "N/A"
        vol_24h = f"${stats['volume_24h']:,.0f}" if stats.get("volume_24h") else "N/A"

        rows.append(
            f"**{idx}. 💎 {name} ({symbol})** {risk_emoji} {score_emoji} | 🌐 {network_name}\n"
            f"💵 {price} | 💧 {liq_val} | 🧠 {fdv_val}\n"
            f"📊 Volume 24h: {vol_24h}\n"
        )

    legend = (
        "**📘 Legend:**\n"
        "🔴 High Risk | 🟡 Medium | 🟢 Low | ❓ Unknown\n"
        "🧠 Score >70 | 🧪 30–70 | ❌ <30 | ❓ Unknown"
    )

    full_description = "\n".join(rows) + "\n\n" + legend

    embed = discord.Embed(
        title="🧠 Top 10 Newest Tokens",
        description=full_description,
        color=0x00ffcc
    )

    await ctx.send(embed=embed)

keep_alive()
bot.run(discord_gem_hunter)
