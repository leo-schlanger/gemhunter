import discord
import logging
from discord import app_commands
from utils.api import fetch_token_stats_geckoterminal, fetch_token_stats_gecko

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
            terminal_data = await fetch_token_stats_geckoterminal(symbol)
            gecko_data = await fetch_token_stats_gecko(symbol)
        except Exception as e:
            logging.error(f"[REACT] Error fetching token data: {e}")
            await interaction.followup.send(f"❌ Failed to fetch data for '{symbol.upper()}'")
            return

        gt_score = terminal_data.get("gt_score")
        price = gecko_data.get("price")
        sym = gecko_data.get("symbol", symbol.upper())

        if gt_score is not None:
            if gt_score >= 70:
                msg = f"🧠 {sym.upper()}? That's a f*cking blue chip, anon! Ape in!"
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
