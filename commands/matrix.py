import discord
import logging
import requests
from discord import app_commands
from config.choices import NETWORK_CHOICES
from utils.api import fetch_token_stats_terminal_by_address, parse_float
from utils.network_labels import NETWORK_LABELS

class MatrixCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="matrix",
            description="List the 10 newest tokens with GT score and risk",
            callback=self.matrix
        )

    @app_commands.describe(network="Filter by blockchain network (or use all)")
    @app_commands.choices(network=NETWORK_CHOICES)
    async def matrix(self, interaction: discord.Interaction, network: app_commands.Choice[str]):
        logging.info(f"[MATRIX] Called by {interaction.user.display_name} for network: {network.value}")

        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            logging.warning("[MATRIX] Failed to defer interaction")

        try:
            if network.value == "all":
                response = requests.get(
                    "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=2400",
                    timeout=15
                )
                tokens = response.json().get("data", [])[:10]
            else:
                response = requests.get(
                    f"https://api.geckoterminal.com/api/v2/networks/{network.value}/tokens?page=1",
                    timeout=15
                )
                tokens_raw = response.json().get("data", [])
                # Ordenar por menor liquidez
                tokens = sorted(tokens_raw, key=lambda t: parse_float(t.get("attributes", {}).get("total_reserve_in_usd")) or 0)[:10]

        except Exception as e:
            logging.error(f"[MATRIX] Failed to fetch token data: {e}")
            await interaction.followup.send("❌ Falha ao buscar os tokens mais recentes.")
            return

        if not tokens:
            await interaction.followup.send(f"❌ Nenhum token recente encontrado para `{network.name}`")
            return

        rows = []
        for idx, token in enumerate(tokens, 1):
            attr = token["attributes"]
            relationships = token.get("relationships", {})

            name = attr.get("name", "Unnamed")
            symbol = attr.get("symbol", "--")
            address = attr.get("address")
            gt_score = parse_float(attr.get("gt_score"))
            network_key = relationships.get("network", {}).get("data", {}).get("id", network.value)
            network_name = NETWORK_LABELS.get(network_key, network_key.capitalize())

            stats = await fetch_token_stats_terminal_by_address(network_key, address)

            score_emoji = "🧠" if gt_score and gt_score >= 70 else "🧪" if gt_score and gt_score >= 30 else "❌" if gt_score is not None else "❓"
            liq = stats.get("liq")
            if liq is not None:
                if liq < 1000 or (gt_score is not None and gt_score < 30):
                    risk_emoji = "🔴"
                elif liq < 10_000:
                    risk_emoji = "🟡"
                else:
                    risk_emoji = "🟢"
            else:
                risk_emoji = "❓"

            liq_val = f"${liq:,.0f}" if liq else "N/A"
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

        embed = discord.Embed(
            title=f"🧠 Gem Matrix — Top 10 Tokens ({network.name})",
            description="\n".join(rows) + "\n\n" + legend,
            color=0x00ffcc
        )

        await interaction.followup.send(embed=embed)
        logging.info(f"[MATRIX] Sent {len(rows)} tokens to {interaction.user.display_name}")
