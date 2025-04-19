import discord
from discord import app_commands
import requests
from config.choices import NETWORK_CHOICES
from utils.network_labels import NETWORK_LABELS
from utils.api import fetch_token_stats_terminal_by_address, parse_float

class MatrixCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="matrix",
            description="List the 10 newest tokens with GT score and risk",
            callback=self.matrix,
        )
        self._params = {
            "network": app_commands.Parameter(
                description="Filter by blockchain network (or use all)",
                choices=NETWORK_CHOICES
            )
        }

    async def matrix(self, interaction: discord.Interaction, network: app_commands.Choice[str]):
        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            pass

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

            score_emoji = "❓"
            if gt_score is not None:
                if gt_score >= 70:
                    score_emoji = "🧠"
                elif gt_score >= 30:
                    score_emoji = "🧪"
                else:
                    score_emoji = "❌"

            risk_emoji = "❓"
            if stats.get("liq") is not None:
                liq = stats["liq"]
                if liq < 1000 or (gt_score and gt_score < 30):
                    risk_emoji = "🔴"
                elif liq < 10_000:
                    risk_emoji = "🟡"
                else:
                    risk_emoji = "🟢"

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
