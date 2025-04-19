import discord
import logging
from discord import app_commands
from utils.dexscreener import search_tokens_dexscreener

class ReactCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="react",
            description="Give a fun crypto reaction based on real token risk (Dexscreener)",
            callback=self.react
        )

    @app_commands.describe(symbol="Token symbol or name")
    async def react(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[REACT] Searching Dexscreener for: {symbol}")

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
                title=f"🎯 Multiple tokens found for '{symbol}'",
                description="\n".join([
                    f"{i+1}. `{t['symbol']}` — {t['name']} ({t['chain']})"
                    for i, t in enumerate(options)
                ]),
                color=0xff9900
            )
            embed.set_footer(text="Reply with a number (1–5) to react.")

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
        liq = token.get("liquidity", {}).get("usd")
        fdv = token.get("fdv")

        # Avaliação do risco
        if liq is not None and fdv is not None:
            if liq >= 1_000_000 or fdv >= 10_000_000:
                emoji = "🧠"
                reaction = f"{emoji} {sym}? That’s a f*cking blue chip, anon! Ape in!"
            elif liq >= 10_000 or fdv >= 1_000_000:
                emoji = "🧪"
                reaction = f"{emoji} {sym}? Mid-tier vibes... might moon, might rug."
            elif liq < 10_000 and fdv < 500_000:
                emoji = "❌"
                reaction = f"{emoji} {sym}? Total trash. Stay away."
            else:
                emoji = "❓"
                reaction = f"{emoji} {sym}? No clear signal. DYOR."
        else:
            emoji = "❓"
            reaction = f"{emoji} {sym}? No data found to react."

        # Legenda
        legend = (
            "\n\n**📘 Legend:**\n"
            "🧠 Liquidity ≥ $1M or FDV ≥ $10M → Blue Chip\n"
            "🧪 Liquidity ≥ $10k or FDV ≥ $1M → Mid-tier\n"
            "❌ Liquidity < $10k and FDV < $500k → High Risk\n"
            "❓ No data available"
        )

        await interaction.followup.send(reaction + legend)
