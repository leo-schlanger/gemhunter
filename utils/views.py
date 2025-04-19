import discord

class TokenSelectionView(discord.ui.View):
    def __init__(self, command_type: str, tokens: list):
        super().__init__(timeout=60)
        self.command_type = command_type
        for token in tokens:
            attr = token["attributes"]
            symbol = attr.get("symbol", "").lower()
            name = attr.get("name", "Unknown")
            self.add_item(TokenButton(symbol, name, command_type))


class TokenButton(discord.ui.Button):
    def __init__(self, symbol: str, name: str, command_type: str):
        label = f"{symbol.upper()} ({name})"
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.symbol = symbol
        self.command_type = command_type

    async def callback(self, interaction: discord.Interaction):
        command = f"/gemhunter {self.command_type} {self.symbol}"
        await interaction.response.send_message(
            f"🔁 Reexecutando: `{command}`\n*Digite o comando acima ou clique para rodar.*", ephemeral=True
        )