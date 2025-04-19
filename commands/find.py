import discord
import logging
from discord import app_commands
from utils.dexscreener import search_tokens_dexscreener
from utils.network_labels import NETWORK_LABELS

class FindCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="find",
            description="Do a deep dive on a token (via Dexscreener)",
            callback=self.find
        )

    @app_commands.describe(symbol="Token symbol or name")
    async def find(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[FIND] Searching Dexscreener for: {symbol}")

        try:
            await interaction.response.defer(thinking=True)
        except:
            pass

        tokens = search_tokens_dexscreener(symbol)
        if not tokens:
            await interaction.followup.send(f"❌ Nenhum token encontrado para `{symbol}`.")
            return

        options = tokens[:5]
        if len(options) == 1:
            token = options[0]
        else:
            embed = discord.Embed(
                title=f"🔍 Tokens encontrados para '{symbol}'",
                description="\n".join([
                    f"{i+1}. `{t['symbol']}` — {t['name']} ({t['chain']})"
                    for i, t in enumerate(options)
                ]),
                color=0x00aaff
            )
            embed.set_footer(text="Digite o número (1–5) para selecionar.")

            await interaction.followup.send(embed=embed)

            def check(m):
                return (
                    m.author.id == interaction.user.id and
                    m.channel == interaction.channel and
                    m.content.isdigit() and
                    1 <= int(m.content) <= len(options)
                )

            try:
                msg = await interaction.client.wait_for("message", timeout=30.0, check=check)
                token = options[int(msg.content) - 1]
            except:
                await interaction.followup.send("⏱️ Tempo esgotado ou entrada inválida.")
                return

        # Montar resposta
        network_name = NETWORK_LABELS.get(token["chain"], token["chain"].capitalize())
        embed = discord.Embed(
            title=f"🔎 {token['symbol']} — {token['name']}",
            description=f"🌐 **Network:** {network_name}\n🏦 **DEX:** {token['dex']}",
            color=0x00ffcc
        )
        embed.add_field(name="Address", value=token['address'], inline=False)
        embed.add_field(name="Pair", value=f"[Ver no Dexscreener]({token['pair_url']})", inline=False)

        await interaction.followup.send(embed=embed)
