import requests
import logging

def search_tokens_dexscreener(query: str):
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logging.error(f"[DEX] HTTP {response.status_code} searching for {query}")
            return []

        data = response.json().get("pairs", [])
        keyword = query.lower()

        # Preparar tokens únicos por baseToken
        seen = set()
        tokens = []
        for pair in data:
            token = pair.get("baseToken", {})
            key = token.get("address")
            if not key or key in seen:
                continue
            seen.add(key)

            tokens.append({
                "symbol": token.get("symbol", "--"),
                "name": token.get("name", "Unknown"),
                "address": token.get("address"),
                "chain": pair.get("chainId", "unknown"),
                "dex": pair.get("dexId", "unknown"),
                "pair_url": pair.get("url", "")
            })

        # Ordenar: exato → menor símbolo
        exact = [t for t in tokens if t["symbol"].lower() == keyword]
        partial = [t for t in tokens if keyword in t["symbol"].lower() or keyword in t["name"].lower()]
        partial = sorted(partial, key=lambda t: len(t["symbol"]))

        return exact + partial

    except Exception as e:
        logging.error(f"[DEX] Error searching token: {e}")
        return []
