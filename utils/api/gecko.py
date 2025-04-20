import requests
import logging
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
                "description": data.get("description", {}).get("en"),
                "source": "coingecko"
            }

    except Exception as e:
        logging.error(f"[API] Error fetching CoinGecko data: {e}")
    return {}
