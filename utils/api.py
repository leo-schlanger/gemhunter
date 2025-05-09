import logging
import requests
import time

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

# In-memory cache
_cached_token_list = None
_last_fetch_time = 0

def get_cached_token_list():
    global _cached_token_list, _last_fetch_time
    cache_duration = 3600  # 1 hour

    if not _cached_token_list or (time.time() - _last_fetch_time) > cache_duration:
        logging.info("[CACHE] Updating token list from CoinGecko")
        response = requests.get("https://api.coingecko.com/api/v3/coins/list", timeout=10)
        if response.status_code == 200:
            _cached_token_list = response.json()
            _last_fetch_time = time.time()
        else:
            logging.error(f"[CACHE] Failed to fetch token list. Status: {response.status_code}")
            return []

    return _cached_token_list

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

async def fetch_token_stats_gecko(symbol):
    try:
        token_list = get_cached_token_list()
        if not token_list:
            logging.error(f"[API] Token list is empty or failed.")
            return {}

        filtered = [token for token in token_list if symbol.lower() in token["symbol"].lower()]

        if not filtered:
            logging.warning(f"[API] No CoinGecko token matches: {symbol}")
            return {}

        filtered.sort(key=lambda x: (x["symbol"].lower() != symbol.lower(), len(x["symbol"])))
        selected_token = filtered[0]
        token_id = selected_token["id"]

        url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
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

async def fetch_token_stats_geckoterminal(symbol, return_multiple=False, separate_matches=False):
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?limit=2400", timeout=10)
        if response.status_code != 200:
            logging.error(f"[API] Unexpected status code: {response.status_code}")
            return [] if return_multiple or separate_matches else {}

        data = response.json().get("data", [])
        matches_exact = []
        matches_similar = []

        for token in data:
            attr = token.get("attributes", {})
            token_symbol = attr.get("symbol", "").lower()
            if token_symbol == symbol.lower():
                matches_exact.append(token)
            elif symbol.lower() in token_symbol:
                matches_similar.append(token)

        matches_exact.sort(key=lambda t: len(t["attributes"].get("symbol", "")))
        matches_similar.sort(key=lambda t: len(t["attributes"].get("symbol", "")))

        if separate_matches:
            return matches_exact, matches_similar

        if return_multiple:
            return matches_exact + matches_similar[:6 - len(matches_exact)]

        if matches_exact:
            token = matches_exact[0]
        elif matches_similar:
            token = matches_similar[0]
        else:
            return {}

        attr = token.get("attributes", {})
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
        return [] if return_multiple or separate_matches else {}

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
