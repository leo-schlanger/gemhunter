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

        seen = set()
        tokens = []
        for pair in data:
            base = pair.get("baseToken", {})
            addr = base.get("address")
            symb = base.get("symbol", "").upper()

            if not addr or (symb, addr) in seen:
                continue

            seen.add((symb, addr))

            tokens.append({
                "symbol": symb,
                "name": base.get("name", "Unknown"),
                "address": addr,
                "chain": pair.get("chainId", "unknown"),
                "dex": pair.get("dexId", "unknown"),
                "fdv": pair.get("fdv"),
                "liquidity": pair.get("liquidity", {}),
                "volume": pair.get("volume", {}),
                "pair_url": pair.get("url", ""),
                "source": "dexscreener"
            })

        # Order: exact symbol first, then partial matches by length
        exact = [t for t in tokens if t["symbol"].lower() == keyword]
        partial = [t for t in tokens if keyword in t["symbol"].lower() or keyword in t["name"].lower()]
        partial = sorted(partial, key=lambda t: len(t["symbol"]))

        return exact + partial

    except Exception as e:
        logging.error(f"[DEX] Error searching token: {e}")
        return []
