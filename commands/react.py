import discord
import logging
from discord import app_commands
from utils.views import TokenSelectionView
from utils.api import (
    fetch_token_stats_geckoterminal,
    fetch_token_stats_terminal_by_address,
    fetch_token_stats_gecko
)

class ReactCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="react",
            description="Give a fun crypto reaction based on GT Score or price",
            callback=self.react
        )

    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[REACT] Requested for symbol: {symbol} by {interaction.user.display_name}")

        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            logging.warning("[REACT] Failed to defer interaction")

        try:
            token_matches = await fetch_token_stats_geckoterminal(symbol, return_multiple=True)

            if not token_matches:
                await interaction.followup.send(f"❌ Nenhum token encontrado com símbolo `{symbol}`")
                return

            if len(token_matches) > 1:
                embed = discord.Embed(
                    title=f"🎭 Múltiplos tokens encontrados para '{symbol}'",
                    description="Selecione o símbolo correto abaixo:",
                    color=0xff9900
                )
                for token in token_matches:
                    attr = token.get("attributes", {})
                    name = attr.get("name", "Unknown")
                    symb = attr.get("symbol", "").upper()
                    network = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
                    embed.add_field(
                        name=f"{name} ({symb})",
                        value=f"Rede: {network.capitalize()} — Use `/gemhunter react {symb.lower()}`",
                        inline=False
                    )
                await interaction.followup.send(embed=embed, view=TokenSelectionView('react', token_matches))
                return

            # único token
            only_token = token_matches[0]
            attr = only_token.get("attributes", {})
            network = only_token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
            address = attr.get("address")

            terminal_data = await fetch_token_stats_terminal_by_address(network, address)
            terminal_data.update({
                "gt_score": attr.get("gt_score"),
                "network": network,
                "address": address
            })

            gecko_data = await fetch_token_stats_gecko(symbol)

        except Exception as e:
            logging.error(f"[REACT] Error fetching token data: {e}")
            await interaction.followup.send(f"❌ Falha ao buscar dados para `{symbol.upper()}`")
            return

        gt_score = terminal_data.get("gt_score")
        price = gecko_data.get("price")
        sym = gecko_data.get("symbol", symbol.upper())

        if gt_score is not None:
            if gt_score >= 70:
                msg = f"🧠 {sym.upper()}? That’s a f*cking blue chip, anon! Ape in!"
            elif gt_score >= 30:
                msg = f"🧪 {sym.upper()}? Mid-tier vibes... might moon, might rug."
            else:
                msg = f"❌ {sym.upper()}? Total trash. Stay away."
        elif price is not None:
            if price >= 10:
                msg = f"🧠 {sym.upper()}? Big boy coin. Safer bet."
            elif price >= 0.1:
                msg = f"🧪 {sym.upper()}? Could go either way."
            else:
                msg = f"❌ {sym.upper()}? Trash tier. Stay cautious."
        else:
            msg = f"❓ {sym.upper()}? No data found to react."

        await interaction.followup.send(content=msg)
        logging.info(f"[REACT] Responded to {symbol.upper()} with: {msg}")
