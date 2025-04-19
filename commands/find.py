import discord
import logging
from discord import app_commands
from utils.dexscreener import search_tokens_dexscreener
from utils.network_labels import NETWORK_LABELS
from humanize import intcomma

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
            await interaction.followup.send(f"❌ No tokens found for `{symbol}`.")
            return

        options = tokens[:5]
        if len(options) == 1:
            token = options[0]
        else:
            embed = discord.Embed(
                title=f"🔍 Tokens found for '{symbol}'",
                description="\n".join([
                    f"{i+1}. `{t['symbol']}` — {t['name']} ({t['chain']})"
                    for i, t in enumerate(options)
                ]),
                color=0x00aaff
            )
            embed.set_footer(text="Reply with a number (1–5) to continue.")

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
                await interaction.followup.send("⏱️ Timed out or invalid input. Cancelled.")
                return

        sym = token["symbol"].upper()
        name = token["name"]
        network = NETWORK_LABELS.get(token["chain"], token["chain"].capitalize())
        liq = token.get("liquidity", {}).get("usd")
        fdv = token.get("fdv")
        vol = token.get("volume", {}).get("usd24h")
        pair_url = token.get("pair_url")

        embed = discord.Embed(
            title=f"🔎 {sym} — {name}",
            color=0x00ffcc,
            description=f"🌐 **Network:** {network} | 🧩 **DEX:** {token['dex']}"
        )
        embed.add_field(name="Address", value=token["address"], inline=False)
        if liq is not None:
            embed.add_field(name="Liquidity", value=f"${intcomma(int(liq))}", inline=True)
        if fdv is not None:
            embed.add_field(name="FDV", value=f"${intcomma(int(fdv))}", inline=True)
        if vol is not None:
            embed.add_field(name="Volume 24h", value=f"${intcomma(int(vol))}", inline=True)
        if pair_url:
            embed.add_field(name="Link", value=f"[View on Dexscreener]({pair_url})", inline=False)

        embed.set_footer(text="Data via Dexscreener — real-time market token info.")

        await interaction.followup.send(embed=embed)
