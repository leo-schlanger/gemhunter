import discord
import logging
from discord import app_commands
from utils.dexscreener import search_tokens_dexscreener
from utils.network_labels import NETWORK_LABELS
from views.token_paginator import TokenPaginatorView

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

        if not tokens:
            await interaction.followup.send(f"❌ No tokens found for `{symbol}`.")
            return

        # Se só um token, continua direto
        if len(tokens) == 1:
            return await self.continue_find(interaction, tokens[0])

        # Caso contrário, abre paginador
        view = TokenPaginatorView(tokens, interaction, callback=self.continue_find)
        await view.start()

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
