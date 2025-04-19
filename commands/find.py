import discord
import logging
from discord import app_commands
from utils.api import (
    fetch_token_stats_geckoterminal,
    fetch_token_stats_terminal_by_address,
    fetch_token_stats_gecko
)
from utils.network_labels import NETWORK_LABELS

class FindCommand(app_commands.Command):
    def __init__(self):
        super().__init__(
            name="find",
            description="Do a deep dive on a specific token",
            callback=self.find
        )

    @app_commands.describe(symbol="Token symbol, e.g., sol")
    async def find(self, interaction: discord.Interaction, symbol: str):
        logging.info(f"[FIND] Requested for symbol: {symbol} by {interaction.user.display_name}")

        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            logging.warning("[FIND] Failed to defer interaction")

        try:
            result = await fetch_token_stats_geckoterminal(symbol, return_multiple=True)

            if isinstance(result, dict):
                token = result

            elif isinstance(result, list) and len(result) > 0:
                exact_matches = [
                    t for t in result
                    if t.get("attributes", {}).get("symbol", "").lower() == symbol.lower()
                ]

                if len(exact_matches) == 1:
                    token = exact_matches[0]
                else:
                    options = exact_matches if exact_matches else result
                    options.sort(key=lambda t: len(t["attributes"].get("symbol", "")))
                    options = options[:5]  # garante até 5 primeiros

                    embed = discord.Embed(
                        title=f"🔍 Múltiplos tokens encontrados para '{symbol}'",
                        description="\n".join([
                            f"{i+1}. `{t['attributes'].get('symbol', '').upper()}` — {t['attributes'].get('name', 'Unknown')}"
                            for i, t in enumerate(options)
                        ]),
                        color=0x00aaff
                    )
                    embed.set_footer(text="Responda com o número (1–5) para continuar.")

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
            logging.error(f"[FIND] Error fetching token data: {e}")
            await interaction.followup.send(f"❌ Token `{symbol.upper()}` não encontrado.")
            return

        name = gecko_data.get("name", "Unknown")
        gt_score = terminal_data.get("gt_score")
        address = terminal_data.get("address", "N/A")
        network = terminal_data.get("network", "unknown")
        liq = terminal_data.get("liq")

        embed = discord.Embed(title=f"🔎 Deep Dive — {name} ({symbol.upper()})", color=0x0099ff)
        embed.add_field(name="Price", value=f"${gecko_data.get('price', 0):.4f}" if gecko_data.get("price") else "N/A", inline=True)
        embed.add_field(name="GT Score", value=f"{gt_score:.1f}" if gt_score else "❓", inline=True)
        embed.add_field(name="FDV", value=f"${gecko_data.get('fdv', 0)/1_000_000:.1f}M" if gecko_data.get("fdv") else "N/A", inline=True)
        embed.add_field(name="24h Volume", value=f"${gecko_data.get('volume_24h', 0):,.0f}" if gecko_data.get("volume_24h") else "N/A", inline=True)
        embed.add_field(name="Liquidity", value=f"${liq:,.0f}" if liq else "N/A", inline=True)
        embed.add_field(name="Network", value=NETWORK_LABELS.get(network, network.capitalize()), inline=True)
        embed.add_field(name="Address", value=address, inline=False)
        embed.add_field(name="Website", value=gecko_data.get("homepage", "N/A"), inline=False)

        desc = gecko_data.get("description")
        if desc:
            embed.add_field(name="Description", value=desc[:1000], inline=False)

        await interaction.followup.send(embed=embed)
        logging.info(f"[FIND] Sent deep dive for {symbol.upper()} to {interaction.user.display_name}")
