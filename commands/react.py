import logging
from discord import app_commands
import discord
from utils.dexscreener import search_tokens_dexscreener

class ReactCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="react",
            description="Give a fun crypto reaction based on liquidity and FDV",
            callback=self.react
        )

    @app_commands.describe(symbol="Token symbol or name")
    async def react(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[REACT] Searching Dexscreener for: {symbol}")
        try:
            await interaction.response.defer(thinking=True)
        except:
            pass

        tokens_raw = search_tokens_dexscreener(symbol)

        seen = set()
        tokens = []
        for t in tokens_raw:
            key = (t["symbol"], t["name"], t["address"], t["chain"])
            if key not in seen:
                seen.add(key)
                tokens.append(t)
            if len(tokens) == 10:
                break

        if not tokens:
            await interaction.followup.send(f"❌ No tokens found for `{symbol}`.")
            return

        if len(tokens) == 1:
            return await self.continue_react(interaction, tokens[0])

        embed = discord.Embed(
            title=f"🎯 Tokens found for '{symbol}'",
            description="\n".join([
                f"{i+1}. `{t['symbol']}` — {t['name']} ({t['chain'].capitalize()})"
                for i, t in enumerate(tokens)
            ]),
            color=0xff9900
        )
        embed.set_footer(text="Reply with a number (1–10) to react.")
        await interaction.followup.send(embed=embed)

        def check(m):
            return (
                m.author.id == interaction.user.id
                and m.channel == interaction.channel
                and m.content.isdigit()
                and 1 <= int(m.content) <= len(tokens)
            )

        try:
            msg = await interaction.client.wait_for("message", timeout=30.0, check=check)
            selected_index = int(msg.content) - 1
            await self.continue_react(interaction, tokens[selected_index])
        except:
            await interaction.followup.send("⏱️ Timed out or invalid input. Cancelled.")
            return

    async def continue_react(self, interaction: discord.Interaction, token):
        sym = token["symbol"].upper()
        liq = token.get("liquidity", {}).get("usd")
        fdv = token.get("fdv")

        if liq is not None and liq >= 1_000_000 or fdv is not None and fdv >= 10_000_000:
            emoji = "🧠"
            msg = f"{emoji} {sym}? That’s a f*cking blue chip, anon! Ape in!"
        elif liq is not None and liq >= 10_000 or fdv is not None and fdv >= 1_000_000:
            emoji = "🧪"
            msg = f"{emoji} {sym}? Mid-tier vibes... might moon, might rug."
        elif liq is not None and liq < 10_000 and (fdv is None or fdv < 500_000):
            emoji = "❌"
            msg = f"{emoji} {sym}? Total trash. Stay away."
        else:
            emoji = "❓"
            msg = f"{emoji} {sym}? No data found to react."

        legend = (
            "\n\n**📘 Legend:**\n"
            "🧠 Liquidity ≥ $1M or FDV ≥ $10M → Blue Chip\n"
            "🧪 Liquidity ≥ $10k or FDV ≥ $1M → Mid-tier\n"
            "❌ Liquidity < $10k and FDV < $500k → High Risk\n"
            "❓ No data available"
        )

        await interaction.followup.send(msg + legend)
