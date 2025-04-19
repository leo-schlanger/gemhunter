import discord
from discord import app_commands
from utils.api import fetch_token_from_geckoterminal_by_symbol, fetch_token_stats_terminal_by_address, fetch_token_stats_gecko
from utils.network_labels import NETWORK_LABELS

class FindCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="find",
            description="Do a deep dive on a specific token",
            callback=self.find,
        )
        self._params = {
            "symbol": app_commands.Parameter(description="Token symbol, e.g., sol")
        }

    async def find(self, interaction: discord.Interaction, symbol: str):
        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            pass

        token = await fetch_token_from_geckoterminal_by_symbol(symbol)
        if not token:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return

        attr = token.get("attributes", {})
        relationships = token.get("relationships", {})
        network_key = relationships.get("network", {}).get("data", {}).get("id", "unknown")
        address = attr.get("address")
        name = attr.get("name", "Unknown")

        terminal_data = await fetch_token_stats_terminal_by_address(network_key, address)
        gecko_data = await fetch_token_stats_gecko(name.lower().replace(" ", "-"))

        embed = discord.Embed(title=f"🔎 Deep Dive — {name} ({symbol.upper()})", color=0x0099ff)
        embed.add_field(name="Price", value=f"${gecko_data.get('price', 0):.4f}" if gecko_data.get("price") else "N/A", inline=True)
        embed.add_field(name="GT Score", value=f"{terminal_data.get('gt_score', '❓')}" if terminal_data.get("gt_score") else "❓", inline=True)
        embed.add_field(name="FDV", value=f"${gecko_data.get('fdv', 0)/1_000_000:.1f}M" if gecko_data.get("fdv") else "N/A", inline=True)
        embed.add_field(name="24h Volume", value=f"${gecko_data.get('volume_24h', 0):,.0f}" if gecko_data.get("volume_24h") else "N/A", inline=True)
        embed.add_field(name="Liquidity", value=f"${terminal_data.get('liq', 0):,.0f}" if terminal_data.get("liq") else "N/A", inline=True)
        embed.add_field(name="Network", value=NETWORK_LABELS.get(network_key, network_key.capitalize()), inline=True)
        embed.add_field(name="Website", value=gecko_data.get("homepage", "N/A"), inline=False)

        desc = gecko_data.get("description")
        if desc:
            embed.add_field(name="Description", value=desc[:1000], inline=False)

        await interaction.followup.send(embed=embed)
