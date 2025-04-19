import discord
from discord import app_commands

class HelpCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="help",
            description="Show all GemHunter commands",
            callback=self.help
        )

    async def help(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            pass

        embed = discord.Embed(title="🤖 Welcome to GemHunter!", color=0x00ffcc)
        embed.add_field(name="/gemhunter matrix", value="List 10 newest tokens with filters", inline=False)
        embed.add_field(name="/gemhunter react <symbol>", value="Crypto reaction with GT Score or Price fallback", inline=False)
        embed.add_field(name="/gemhunter find <symbol>", value="Deep analysis of token using CoinGecko + GT Score", inline=False)
        embed.add_field(name="/gemhunter help", value="Show all available GemHunter commands", inline=False)

        await interaction.followup.send(embed=embed)
