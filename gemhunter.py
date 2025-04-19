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

class GemHunterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="matrix", description="List the 10 newest tokens with GT score and risk")
    async def matrix(self, interaction: discord.Interaction):
        await interaction.response.defer()
        base_url = "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated"
        tokens = requests.get(base_url).json().get("data", [])[:10]

        rows = []
        for idx, token in enumerate(tokens, 1):
            attr = token["attributes"]
            net = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
            stats = await fetch_token_stats(net, attr.get("address"))

            name = attr.get("name", "Unnamed")
            symbol = attr.get("symbol", "--")
            network = NETWORK_LABELS.get(net, net)

            gt_score = stats.get("gt_score")
            score_emoji = "🧠" if gt_score and gt_score >= 70 else "🧪" if gt_score and gt_score >= 30 else "❌" if gt_score else "❓"

            if stats.get("liq") is not None and stats.get("fdv") is not None:
                liq = stats["liq"]
                fdv = stats["fdv"]
                risk_emoji = "🔴" if liq < 1000 or fdv > 10_000_000 else "🟡" if liq < 10_000 or fdv > 1_000_000 else "🟢"
            else:
                risk_emoji = "❓"

            price = f"${stats['price']:.6f}" if stats.get("price") else "N/A"
            liq_val = f"${stats['liq']:,.0f}" if stats.get("liq") else "N/A"
            fdv_val = f"${stats['fdv']/1_000_000:.1f}M" if stats.get("fdv") else "N/A"
            vol_24h = f"${stats['volume_24h']:,.0f}" if stats.get("volume_24h") else "N/A"

            rows.append(
                f"**{idx}. 💎 {name} ({symbol})** {risk_emoji} {score_emoji} | 🌐 {network}\n"
                f"💵 {price} | 💧 {liq_val} | 🧠 {fdv_val}\n"
                f"📊 Volume 24h: {vol_24h}\n"
            )

        legend = (
            "**📘 Legend:**\n"
            "🔴 High Risk | 🟡 Medium | 🟢 Low | ❓ Unknown\n"
            "🧠 Score >70 | 🧪 30–70 | ❌ <30 | ❓ Unknown"
        )

        embed = discord.Embed(
            title="🧠 Gem Matrix — Top 10 New Tokens",
            description="\n".join(rows) + "\n\n" + legend,
            color=0x00ffcc
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="react", description="Give a fun crypto reaction based on GT Score")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        base_url = "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated"
        data = requests.get(base_url).json().get("data", [])
        for token in data:
            attr = token["attributes"]
            if attr.get("symbol", "").lower() == symbol.lower():
                score = parse_float(attr.get("gt_score"))
                if score is None:
                    msg = "❓ I can't even score this one. Too early, maybe?"
                elif score >= 70:
                    msg = f"🧠 {symbol.upper()}? That's a f*cking blue chip, anon! Ape in!"
                elif score >= 30:
                    msg = f"🧪 {symbol.upper()}? Meh... mid-tier stuff. Might moon, might rug."
                else:
                    msg = f"❌ {symbol.upper()}? Bro that's absolute sh*t. Get out before it rugs."
                await interaction.response.send_message(msg)
                return
        await interaction.response.send_message(f"❌ Token '{symbol}' not found in recent listings.")

    @app_commands.command(name="find", description="Do a deep dive on a specific token")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        base_url = "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated"
        data = requests.get(base_url).json().get("data", [])
        for token in data:
            attr = token["attributes"]
            net = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
            if attr.get("symbol", "").lower() == symbol.lower():
                stats = await fetch_token_stats(net, attr.get("address"))
                name = stats.get("name", "Unknown")
                score = stats.get("gt_score")
                emoji = "🧠" if score and score > 70 else "🧪" if score and score > 30 else "❌"
                score_str = f"{emoji} {score:.2f}" if score else "❓ Unknown"
                embed = discord.Embed(title=f"🔎 Deep Dive — {name} ({symbol.upper()})", color=0x0099ff)
                embed.add_field(name="Network", value=NETWORK_LABELS.get(net, net), inline=True)
                embed.add_field(name="GT Score", value=score_str, inline=True)
                embed.add_field(name="Website", value=stats.get("site", "N/A"), inline=False)
                embed.add_field(name="Description", value=stats.get("desc", "No description found."), inline=False)
                await interaction.response.send_message(embed=embed)
                return
        await interaction.response.send_message(f"❌ Token '{symbol}' not found in recent listings.")

    @app_commands.command(name="help", description="Show all GemHunter commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Welcome to GemHunter!", color=0x00ffcc)
        embed.add_field(name="/gemhunter matrix", value="Gem Matrix\nList the 10 newest tokens with risk, GT Score, volume, and network info.", inline=False)
        embed.add_field(name="/gemhunter react <symbol>", value="Shit or Hit?\nGet a degenerate crypto reaction based on GT Score.", inline=False)
        embed.add_field(name="/gemhunter find <symbol>", value="Deep Dive\nSee a full analysis of a token with score, description, and link.", inline=False)
        await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")
    await bot.tree.sync()

async def setup():
    bot.tree.add_command(GemHunterCog(bot))

keep_alive()

bot.tree.add_command(GemHunterCog(bot))
bot.run(discord_gem_hunter)
