import discord

class TokenSelectionView(discord.ui.View):
    def __init__(self, command_type: str, tokens: list, callback, timeout=30):
        super().__init__(timeout=timeout)
        self.callback_fn = callback
        for token in tokens[:6]:
            attr = token["attributes"]
            symbol = attr.get("symbol", "").lower()
            name = attr.get("name", "Unknown")
            self.add_item(TokenButton(symbol, name, self.callback_fn))


class TokenButton(discord.ui.Button):
    def __init__(self, symbol: str, name: str, callback_fn):
        label = f"{symbol.upper()} ({name})"
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.symbol = symbol
        self.callback_fn = callback_fn

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.callback_fn(interaction, self.symbol)