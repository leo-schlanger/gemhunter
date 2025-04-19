import discord

class TokenPaginatorView(discord.ui.View):
    def __init__(self, tokens, interaction, callback):
        super().__init__(timeout=30)
        self.tokens = tokens
        self.interaction = interaction
        self.callback = callback
        self.page = 0
        self.message = None

    async def start(self):
        self.message = await self.interaction.followup.send(embed=self.build_embed(), view=self)

    def build_embed(self):
        start = self.page * 5
        end = start + 5
        embed = discord.Embed(
            title=f"🔍 Tokens encontrados para '{self.interaction.data.get('options', [{}])[0].get('value', '')}'",
            description="Digite o número (1–5) para selecionar.",
            color=0x00ffcc
        )
        for i, token in enumerate(self.tokens[start:end], start=1):
            symbol = token["symbol"]
            name = token["name"]
            network = token["chain"].capitalize()
            embed.add_field(name=f"{i}. `{symbol}` — {name} ({network})", value="⠀", inline=False)
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await self.message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🔄 Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_page = (len(self.tokens) - 1) // 5
        if self.page < max_page:
            self.page += 1
            await self.message.edit(embed=self.build_embed(), view=self)