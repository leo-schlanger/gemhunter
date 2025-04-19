import discord
import logging
from discord import app_commands
from utils.api import fetch_token_stats_geckoterminal, fetch_token_stats_gecko
from utils.network_labels import NETWORK_LABELS

class FindCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="find",
            description="Do a deep dive on a specific token",
            callback=self.find
        )

    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[FIND] Requested for symbol: {symbol} by {interaction.user.display_name}")

        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            logging.warning("[FIND] Failed to defer interaction")

        try:
            terminal_data = await fetch_token_stats_geckoterminal(symbol)
            gecko_data = await fetch_token_stats_gecko(symbol)
        except Exception as e:
            logging.error(f"[FIND] Error fetching token data: {e}")
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return

        name = gecko_data.get("name", "Unknown")
        gt_score = terminal_data.get("gt_score")
        address = terminal_data.get("address", "N/A")
        network = terminal_data.get("network", "unknown")
        liq = terminal_data.get("liq")

        embed = discord.Embed(title=f"🔎 Deep Dive — {name} ({symbol.upper()})", color=0x0099ff)
        embed.add_field(name="Price", value=f"${gecko_data.get('price', 0):.4f}" if gecko_data.get("price") else "N/A", inline=True)
        embed.add_field(name="GT Score", value=f"{gt_score:.1f}" if gt_score else "❓", inline=True)
        embed.add_field(name="FDV", value=f"${gecko_data.get('fdv', 0)/1_000_000:.1f}M" if gecko_data.get("fdv") else "N/A", inline=True)
        embed.add_field(name="24h Volume", value=f"${gecko_data.get('volume_24h', 0):,.0f}" if gecko_data.get("volume_24h") else "N/A", inline=True)
        embed.add_field(name="Liquidity", value=f"${liq:,.0f}" if liq else "N/A", inline=True)
        embed.add_field(name="Network", value=NETWORK_LABELS.get(network, network.capitalize()), inline=True)
        embed.add_field(name="Address", value=address, inline=False)
        embed.add_field(name="Website", value=gecko_data.get("homepage", "N/A"), inline=False)

        desc = gecko_data.get("description")
        if desc:
            embed.add_field(name="Description", value=desc[:1000], inline=False)

        await interaction.followup.send(embed=embed)
        logging.info(f"[FIND] Sent deep dive for {symbol.upper()} to {interaction.user.display_name}")
