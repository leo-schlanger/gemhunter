import discord
from discord import app_commands
from utils.api import fetch_token_from_geckoterminal_by_symbol, fetch_token_stats_terminal_by_address, fetch_token_stats_gecko

class ReactCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="react",
            description="Give a fun crypto reaction based on GT Score or price",
            callback=self.react,
        )
        self._params = {
            "symbol": app_commands.Parameter(description="Token symbol, e.g., sol")
        }

    async def react(self, interaction: discord.Interaction, symbol: str):
        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            pass

        token = await fetch_token_from_geckoterminal_by_symbol(symbol)
        if not token:
            await interaction.followup.send(f"❌ Token '{symbol.upper()}' not found.")
            return

        attr = token["attributes"]
        address = attr.get("address")
        network = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")

        terminal_data = await fetch_token_stats_terminal_by_address(network, address)
        gt_score = terminal_data.get("gt_score")

        gecko_data = await fetch_token_stats_gecko(attr.get("name", "").lower().replace(" ", "-"))
        price = gecko_data.get("price")

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
