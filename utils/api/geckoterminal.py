import requests
import logging
from .gecko import parse_float

async def fetch_token_stats_terminal_by_address(network, address):
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            attr = response.json().get("data", {}).get("attributes", {})
            return {
                "liq": parse_float(attr.get("total_reserve_in_usd")),
                "gt_score": parse_float(attr.get("gt_score")),
                "source": "geckoterminal"
            }
    except Exception as e:
        logging.error(f"[API] Error fetching terminal token stats: {e}")
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
