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
            # All networks
            if network.value == "all":
                url = "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=2400"
            else:
                url = f"https://api.geckoterminal.com/api/v2/networks/{network.value}/tokens?page=1"

            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                logging.error(f"[MATRIX] Failed to fetch token data: HTTP {response.status_code}")
                await interaction.followup.send(f"❌ Erro {response.status_code} ao buscar tokens da rede `{network.name}`.")
                return

            try:
                data = response.json()
            except Exception as e:
                logging.error(f"[MATRIX] Invalid JSON response: {e}")
                await interaction.followup.send(f"❌ Resposta inválida da API. Tente novamente mais tarde.")
                return

            tokens = data.get("data", [])
            if not isinstance(tokens, list):
                logging.error(f"[MATRIX] Unexpected format: {tokens}")
                await interaction.followup.send(f"❌ Resposta inesperada da API. Tente novamente.")
                return

            if network.value == "all":
                tokens = tokens[:10]
            else:
                tokens.sort(key=lambda t: parse_float(t.get("attributes", {}).get("total_reserve_in_usd")) or 0)
                tokens = tokens[:10]

        except Exception as e:
            logging.error(f"[MATRIX] Exception: {e}")
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
