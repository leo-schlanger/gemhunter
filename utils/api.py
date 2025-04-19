import requests
import logging

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

async def fetch_token_stats_terminal_by_address(network, address):
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            attr = response.json().get("data", {}).get("attributes", {})
            return {
                "liq": parse_float(attr.get("total_reserve_in_usd")),
                "gt_score": parse_float(attr.get("gt_score"))
            }
    except Exception as e:
        logging.error(f"[API] Error fetching terminal token stats: {e}")
    return {}

async def fetch_token_stats_gecko(gecko_id_or_symbol):
    url = f"https://api.coingecko.com/api/v3/coins/{gecko_id_or_symbol}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", {})
            return {
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "price": parse_float(market_data.get("current_price", {}).get("usd")),
                "volume_24h": parse_float(market_data.get("total_volume", {}).get("usd")),
                "fdv": parse_float(market_data.get("fully_diluted_valuation", {}).get("usd")),
                "homepage": data.get("links", {}).get("homepage", [None])[0],
                "description": data.get("description", {}).get("en")
            }
    except Exception as e:
        logging.error(f"[API] Error fetching CoinGecko data: {e}")
    return {}

async def fetch_token_stats_geckoterminal(symbol):
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=1000", timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            for token in data:
                attr = token.get("attributes", {})
                if attr.get("symbol", "").lower() == symbol.lower():
                    network = token.get("relationships", {}).get("network", {}).get("data", {}).get("id", "unknown")
                    address = attr.get("address")
                    stats = await fetch_token_stats_terminal_by_address(network, address)
                    stats.update({
                        "gt_score": parse_float(attr.get("gt_score")),
                        "network": network,
                        "address": address
                    })
                    return stats
    except Exception as e:
        logging.error(f"[API] Error fetching GeckoTerminal data: {e}")
    return {}

async def fetch_token_from_geckoterminal_by_symbol(symbol):
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=1000", timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            for token in data:
                attr = token.get("attributes", {})
                if attr.get("symbol", "").lower() == symbol.lower():
                    return token
    except Exception as e:
        logging.error(f"[API] Error fetching GeckoTerminal token by symbol: {e}")
    return None
