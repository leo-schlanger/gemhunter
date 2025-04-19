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
        embed = discord.Embed(
            title="🧠 GemHunter — Command Guide",
            description="Welcome to GemHunter, your crypto alpha radar.\nHere’s what I can do:",
            color=0x00ffcc
        )

        embed.add_field(
            name="💎 /gemhunter matrix [network]",
            value="Shows the 10 newest tokens with GT Score and risk, filtered by network.",
            inline=False
        )

        embed.add_field(
            name="📊 /gemhunter find <symbol>",
            value="Deep dive into a token with FDV, liquidity, volume, network, address, and Dexscreener link.",
            inline=False
        )

        embed.add_field(
            name="😎 /gemhunter react <symbol>",
            value="Gives a fun crypto-style reaction based on liquidity and FDV of a token.",
            inline=False
        )

        embed.add_field(
            name="📘 /gemhunter help",
            value="Shows this guide with all available commands.",
            inline=False
        )

        embed.add_field(
            name="📎 Legend",
            value="🧠 Blue Chip  |  🧪 Mid-tier  |  ❌ Trash  |  ❓ Unknown",
            inline=False
        )

        embed.set_footer(text="Powered by GeckoTerminal & Dexscreener • Follow the alpha 🧠")

        await interaction.response.send_message(embed=embed)
