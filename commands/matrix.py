import discord
import logging
from discord import app_commands
from config.choices import NETWORK_CHOICES
from utils.api import fetch_recent_tokens_dexscreener
from utils.network_labels import NETWORK_LABELS
from humanize import intcomma

class MatrixCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="matrix",
            description="List the 10 newest tokens with volume and risk",
            callback=self.matrix
        )

    @app_commands.describe(network="Select a blockchain network or 'all'")
    @app_commands.choices(network=NETWORK_CHOICES)
    async def matrix(self, interaction: discord.Interaction, network: app_commands.Choice[str]):
        logging.info(f"[MATRIX] Called by {interaction.user.display_name} for network: {network.value}")

        try:
            await interaction.response.defer(thinking=True)
        except:
            pass

        tokens = fetch_recent_tokens_dexscreener(network.value)
        if not tokens:
            await interaction.followup.send(f"❌ No tokens found for network `{network.name}`.")
            return

        tokens = tokens[:10]
        rows = []
        for idx, token in enumerate(tokens, 1):
            name = token["name"]
            symbol = token["symbol"]
            liq = token.get("liquidity", {}).get("usd")
            fdv = token.get("fdv")
            chain = token.get("chain")
            net = NETWORK_LABELS.get(chain, chain.capitalize())

            # Risco baseado na liquidez e FDV
            if liq is not None and fdv is not None:
                if liq >= 1_000_000 or fdv >= 10_000_000:
                    risk = "🧠"
                elif liq >= 10_000 or fdv >= 1_000_000:
                    risk = "🧪"
                elif liq < 10_000 and fdv < 500_000:
                    risk = "❌"
                else:
                    risk = "❓"
            else:
                risk = "❓"

            rows.append(
                f"**{idx}. 💎 {name} ({symbol})** {risk} | 🌐 {net}"
                f"💧 Liquidity: ${intcomma(int(liq)) if liq else 'N/A'} | FDV: ${intcomma(int(fdv)) if fdv else 'N/A'}"
                f"[Dexscreener ↗]({token['pair_url']})"
            )

        legend = (
            "**📘 Legend:**"
            "🧠 Liquidity ≥ $1M or FDV ≥ $10M → Blue Chip"
            "🧪 Liquidity ≥ $10k or FDV ≥ $1M → Mid-tier"
            "❌ Liquidity < $10k and FDV < $500k → High Risk"
            "❓ No data available"
        )

        embed = discord.Embed(
            title=f"🧠 Gem Matrix — Top 10 Tokens ({network.name})",
            description="".join(rows) + "" + legend,
            color=0x00ffcc
        )

        await interaction.followup.send(embed=embed)
        logging.info(f"[MATRIX] Sent {len(rows)} tokens to {interaction.user.display_name}")