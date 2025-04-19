import discord
import logging
from discord import app_commands
from utils.api import (
    fetch_token_stats_geckoterminal,
    fetch_token_stats_terminal_by_address,
    fetch_token_stats_gecko
)

class ReactCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="react",
            description="Give a fun crypto reaction based on GT Score or price",
            callback=self.react
        )

    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def react(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[REACT] Requested for symbol: {symbol} by {interaction.user.display_name}")

        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            logging.warning("[REACT] Failed to defer interaction")

        try:
            result = await fetch_token_stats_geckoterminal(symbol, return_multiple=True)

            if isinstance(result, dict):
                token = result

            elif isinstance(result, list) and len(result) > 0:
                keyword = symbol.lower()
                exact = []
                partial = []

                for t in result:
                    attr = t.get("attributes", {})
                    sym = attr.get("symbol", "").lower()
                    name = attr.get("name", "").lower()

                    if sym == keyword:
                        exact.append(t)
                    elif keyword in sym or keyword in name:
                        partial.append(t)

                options = exact + sorted(partial, key=lambda t: len(t["attributes"].get("symbol", "")))
                options = options[:5]

                if not options:
                    await interaction.followup.send(f"❌ Nenhum token encontrado com símbolo `{symbol}`")
                    return

                if len(options) == 1:
                    token = options[0]
                else:
                    embed = discord.Embed(
                        title=f"🎯 Vários tokens encontrados para '{symbol}'",
                        description="\n".join([
                            f"{i+1}. `{t['attributes'].get('symbol', '').upper()}` — {t['attributes'].get('name', 'Unknown')}"
                            for i, t in enumerate(options)
                        ]),
                        color=0xff9900
                    )
                    embed.set_footer(text="Digite o número (1–5) para escolher.")

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
                        selected_index = int(msg.content) - 1
                        token = options[selected_index]
                    except:
                        await interaction.followup.send("⏱️ Tempo esgotado ou resposta inválida. Operação cancelada.")
                        return
            else:
                await interaction.followup.send(f"❌ Nenhum token encontrado com símbolo `{symbol}`")
                return

            attr = token.get("attributes", {})
            network = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
            address = attr.get("address")

            terminal_data = await fetch_token_stats_terminal_by_address(network, address)
            terminal_data.update({
                "gt_score": attr.get("gt_score"),
                "network": network,
                "address": address
            })

            gecko_data = await fetch_token_stats_gecko(symbol)

        except Exception as e:
            logging.error(f"[REACT] Error fetching token data: {e}")
            await interaction.followup.send(f"❌ Falha ao buscar dados para `{symbol.upper()}`")
            return

        gt_score = terminal_data.get("gt_score")
        price = gecko_data.get("price")
        sym = gecko_data.get("symbol", symbol.upper())

        if gt_score is not None:
            if gt_score >= 70:
                msg = f"🧠 {sym.upper()}? That’s a f*cking blue chip, anon! Ape in!"
            elif gt_score >= 30:
                msg = f"🧪 {sym.upper()}? Mid-tier vibes... might moon, might rug."
            else:
                msg = f"❌ {sym.upper()}? Total trash. Stay away."
        elif price is not None:
            if price >= 10:
                msg = f"🧠 {sym.upper()}? Big boy coin. Safer bet."
            elif price >= 0.1:
                msg = f"🧪 {sym.upper()}? Could go either way."
            else:
                msg = f"❌ {sym.upper()}? Trash tier. Stay cautious."
        else:
            msg = f"❓ {sym.upper()}? No data found to react."

        await interaction.followup.send(content=msg)
        logging.info(f"[REACT] Responded to {symbol.upper()} with: {msg}")
