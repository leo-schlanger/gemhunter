import requests
import logging

def fetch_recent_tokens_dexscreener(network="all"):
    try:
        url = "https://api.dexscreener.com/latest/dex/pairs"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logging.error(f"[DEX] Failed to fetch recent pairs. HTTP {response.status_code}")
            return []

        data = response.json().get("pairs", [])
        seen = set()
        results = []

        for pair in data:
            base = pair.get("baseToken", {})
            quote = pair.get("quoteToken", {})
            chain = pair.get("chainId", "")
            addr = base.get("address")
            symb = base.get("symbol", "")

            if not addr or (symb, addr) in seen:
                continue

            if network != "all" and chain != network:
                continue

            quote_sym = quote.get("symbol", "").lower()
            if not any(stable in quote_sym for stable in ["usd", "usdt", "usdc"]):
                continue

            seen.add((symb, addr))
            results.append({
                "symbol": symb.upper(),
                "name": base.get("name", "Unknown"),
                "address": addr,
                "chain": chain,
                "dex": pair.get("dexId", "unknown"),
                "fdv": pair.get("fdv"),
                "liquidity": pair.get("liquidity", {}),
                "volume": pair.get("volume", {}),
                "pair_url": pair.get("url", "")
            })

            if len(results) >= 100:
                break

        return results

    except Exception as e:
        logging.error(f"[DEX] Error fetching recent tokens: {e}")
        return []
