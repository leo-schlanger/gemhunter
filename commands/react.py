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
            matches_exact, matches_similar = await fetch_token_stats_geckoterminal(symbol, separate_matches=True)

            if not matches_exact and not matches_similar:
                await interaction.followup.send(f"❌ Nenhum token encontrado com símbolo `{symbol}`")
                return

            token_matches = matches_exact if matches_exact else matches_similar

            if len(token_matches) == 1:
                only_token = token_matches[0]
            else:
                async def handle_selection(inter: discord.Interaction, selected_symbol: str):
                    await self.react(inter, selected_symbol)

                embed = discord.Embed(
                    title=f"🎭 Múltiplos tokens encontrados para '{symbol}'",
                    description="Selecione o símbolo correto abaixo:",
                    color=0xff9900
                )
                await interaction.followup.send(
                    embed=embed,
                    view=TokenSelectionView("react", token_matches, handle_selection)
                )
                return

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
