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

        tokens_raw = search_tokens_dexscreener(symbol)

        # Deduplicar por symbol + name + address + chain
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
            return await self.continue_find(interaction, tokens[0])

        # Menu para usuário escolher digitando número
        embed = discord.Embed(
            title=f"🔍 Tokens found for '{symbol}'",
            description="\n".join([
                f"{i+1}. `{t['symbol']}` — {t['name']} ({t['chain'].capitalize()})"
                for i, t in enumerate(tokens)
            ]),
            color=0x00ffcc
        )
        embed.set_footer(text="Reply with a number (1–10) to select a token.")
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
            await self.continue_find(interaction, tokens[selected_index])
        except:
            await interaction.followup.send("⏱️ Timed out or invalid input. Cancelled.")
            return

    async def continue_find(self, interaction: discord.Interaction, token):
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
        if liq:
            embed.add_field(name="Liquidity", value=f"${liq:,.0f}", inline=True)
        if fdv:
            embed.add_field(name="FDV", value=f"${fdv:,.0f}", inline=True)
        if vol:
            embed.add_field(name="Volume 24h", value=f"${vol:,.0f}", inline=True)
        if pair_url:
            embed.add_field(name="Link", value=f"[View on Dexscreener]({pair_url})", inline=False)

        embed.set_footer(text="Data via Dexscreener — real-time token info.")
        await interaction.followup.send(embed=embed)
