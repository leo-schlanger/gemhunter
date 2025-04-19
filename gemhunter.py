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

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

async def fetch_token_stats_gecko(gecko_id):
    url = f"https://api.coingecko.com/api/v3/coins/{gecko_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", {})
            return {
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "price": parse_float(market_data.get("current_price", {}).get("usd")),
                "volume_24h": parse_float(market_data.get("total_volume", {}).get("usd")),
                "fdv": parse_float(market_data.get("fully_diluted_valuation", {}).get("usd")),
                "homepage": data.get("links", {}).get("homepage", [None])[0],
                "description": data.get("description", {}).get("en")
            }
    except Exception as e:
        print(f"❌ Error fetching CoinGecko data: {e}")
    return {}

async def fetch_token_stats_geckoterminal(symbol):
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=100", timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            for token in data:
                attr = token.get("attributes", {})
                if attr.get("symbol", "").lower() == symbol.lower():
                    network = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
                    address = attr.get("address")
                    stats = await fetch_token_stats_terminal_by_address(network, address)
                    stats["gt_score"] = parse_float(attr.get("gt_score"))
                    stats["network"] = NETWORK_LABELS.get(network, network.capitalize())
                    stats["address"] = address
                    return stats
    except Exception as e:
        print(f"❌ Error fetching GeckoTerminal data: {e}")
    return {}

async def fetch_token_stats_terminal_by_address(network, address):
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            attr = response.json().get("data", {}).get("attributes", {})
            return {
                "liq": parse_float(attr.get("total_reserve_in_usd")),
            }
    except Exception as e:
        print(f"❌ Error fetching terminal token stats: {e}")
    return {}

async def prompt_token_selection(interaction, symbol, options):
    msg = f"⚠️ Found multiple tokens with symbol `{symbol}`:\n"
    for i, token in enumerate(options):
        name = token.get("name", "Unknown")
        token_id = token.get("id", "N/A")
        msg += f"**{i+1}.** {name} — `{token_id}`\n"
    msg += f"\nPlease reply with the number of your choice (1–{len(options)}). You have 30 seconds."

    await interaction.followup.send(msg)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        reply = await bot.wait_for("message", timeout=30.0, check=check)
        index = int(reply.content.strip()) - 1
        if 0 <= index < len(options):
            return options[index]
    except (asyncio.TimeoutError, ValueError):
        await interaction.followup.send("❌ Timeout or invalid selection. Operation cancelled.")
    return None

class GemHunter(app_commands.Group):
    def __init__(self):
        super().__init__(name="gemhunter", description="The ultimate gem analyzer")

    @app_commands.command(name="matrix", description="List the 10 newest tokens with GT score and risk")
    @app_commands.describe(network="Filter by blockchain network (or use all)")
    @app_commands.choices(network=NETWORK_CHOICES)
    async def matrix(self, interaction: discord.Interaction, network: app_commands.Choice[str]):
        await interaction.response.defer(thinking=True)
        
        try:
            data = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=100", timeout=10).json()
        except:
            await interaction.followup.send("❌ Failed to fetch token data.")
            return

        tokens = data.get("data", [])
        filtered = [t for t in tokens if network.value == "all" or t.get("relationships", {}).get("network", {}).get("data", {}).get("id") == network.value][:10]

        rows = []
        for idx, token in enumerate(filtered, 1):
            attr = token["attributes"]
            relationships = token.get("relationships", {})

            name = attr.get("name", "Unnamed")
            symbol = attr.get("symbol", "--")
            address = attr.get("address")
            gt_score = parse_float(attr.get("gt_score"))
            network_key = relationships.get("network", {}).get("data", {}).get("id", "unknown")
            network_name = NETWORK_LABELS.get(network_key, network_key.capitalize())

            stats = await fetch_token_stats_terminal_by_address(network_key, address)

            if gt_score is not None:
                if gt_score >= 70:
                    score_emoji = "🧠"
                elif gt_score >= 30:
                    score_emoji = "🧪"
                else:
                    score_emoji = "❌"
            else:
                score_emoji = "❓"

            if stats.get("liq") is not None:
                liq = stats["liq"]
                if liq < 1000 or gt_score and gt_score < 30:
                    risk_emoji = "🔴"
                elif liq < 10_000:
                    risk_emoji = "🟡"
                else:
                    risk_emoji = "🟢"
            else:
                risk_emoji = "❓"

            liq_val = f"${stats['liq']:,.0f}" if stats.get("liq") else "N/A"
            fdv_val = f"{gt_score:.1f}" if gt_score is not None else "❓"

            rows.append(
                f"**{idx}. 💎 {name} ({symbol})** {risk_emoji} {score_emoji} | 🌐 {network_name}\n"
                f"💧 Liquidity: {liq_val} | 🧠 GT Score: {fdv_val}\n"
            )

        legend = (
            "**📘 Legend:**\n"
            "🔴 High Risk | 🟡 Medium | 🟢 Low | ❓ Unknown\n"
            "🧠 Score >70 | 🧪 30–70 | ❌ <30 | ❓ Unknown"
        )

        embed = discord.Embed(title=f"🧠 Gem Matrix — Top 10 Tokens ({network.name})", description="\n".join(rows) + "\n\n" + legend, color=0x00ffcc)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="react", description="Give a fun crypto reaction based on GT Score or price")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(thinking=True)

        response = requests.get("https://api.coingecko.com/api/v3/coins/list")
        token_list = response.json() if response.status_code == 200 else []
        matches = [t for t in token_list if t.get("symbol", "").lower() == symbol.lower()]

        if not matches:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return

        selected = matches[0] if len(matches) == 1 else await prompt_token_selection(interaction, symbol, matches)
        if not selected:
            return

        gecko_data = await fetch_token_stats_gecko(selected['id'])
        terminal_data = await fetch_token_stats_geckoterminal(symbol)

        gt_score = terminal_data.get("gt_score")
        price = gecko_data.get("price")
        symbol = gecko_data.get("symbol", symbol.upper())

        if gt_score is not None:
            if gt_score >= 70:
                msg = f"🧠 {symbol.upper()}? That's a f*cking blue chip, anon! Ape in!"
            elif gt_score >= 30:
                msg = f"🧪 {symbol.upper()}? Mid-tier vibes... might moon, might rug."
            else:
                msg = f"❌ {symbol.upper()}? Total trash. Stay away."
        elif price is not None:
            if price >= 10:
                msg = f"🧠 {symbol.upper()}? Big boy coin. Safer bet."
            elif price >= 0.1:
                msg = f"🧪 {symbol.upper()}? Could go either way."
            else:
                msg = f"❌ {symbol.upper()}? Trash tier. Stay cautious."
        else:
            msg = f"❓ {symbol.upper()}? No data found to react."

        await interaction.followup.send(content=msg)

    @app_commands.command(name="find", description="Do a deep dive on a specific token")
    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(thinking=True)
        
        response = requests.get("https://api.coingecko.com/api/v3/coins/list")
        token_list = response.json() if response.status_code == 200 else []
        matches = [t for t in token_list if t.get("symbol", "").lower() == symbol.lower()]

        if not matches:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return

        selected = matches[0] if len(matches) == 1 else await prompt_token_selection(interaction, symbol, matches)
        if not selected:
            return

        gecko_data = await fetch_token_stats_gecko(selected['id'])
        terminal_data = await fetch_token_stats_geckoterminal(symbol)

        embed = discord.Embed(title=f"🔎 Deep Dive — {gecko_data.get('name', 'Unknown')} ({symbol.upper()})", color=0x0099ff)
        embed.add_field(name="Price", value=f"${gecko_data.get('price', 0):.4f}" if gecko_data.get("price") else "N/A", inline=True)
        embed.add_field(name="GT Score", value=f"{terminal_data.get('gt_score', '❓')}" if terminal_data.get("gt_score") else "❓", inline=True)
        embed.add_field(name="FDV", value=f"${gecko_data.get('fdv', 0)/1_000_000:.1f}M" if gecko_data.get("fdv") else "N/A", inline=True)
        embed.add_field(name="24h Volume", value=f"${gecko_data.get('volume_24h', 0):,.0f}" if gecko_data.get("volume_24h") else "N/A", inline=True)
        embed.add_field(name="Liquidity", value=f"${terminal_data.get('liq', 0):,.0f}" if terminal_data.get("liq") else "N/A", inline=True)
        embed.add_field(name="Network", value=terminal_data.get("network", "❓"), inline=True)
        embed.add_field(name="Website", value=gecko_data.get("homepage", "N/A"), inline=False)

        desc = gecko_data.get("description")
        if desc:
            embed.add_field(name="Description", value=desc[:1000], inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="Show all GemHunter commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Welcome to GemHunter!", color=0x00ffcc)
        embed.add_field(name="/gemhunter matrix", value="List 10 newest tokens with filters", inline=False)
        embed.add_field(name="/gemhunter react <symbol>", value="Crypto reaction with GT Score or Price fallback", inline=False)
        embed.add_field(name="/gemhunter find <symbol>", value="Deep analysis of token using CoinGecko + GT Score", inline=False)
        await interaction.response.send_message(embed=embed)

bot.tree.add_command(GemHunter())

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")
    await bot.tree.sync()

bot.run(discord_gem_hunter)
