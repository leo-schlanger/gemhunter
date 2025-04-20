# API Module — Token Data Providers

This folder organizes all external API integrations used to fetch token-related data.

---

## 🧭 Responsibilities

| API            | Provides...                                                                 |
|----------------|------------------------------------------------------------------------------|
| `gecko.py`     | CoinGecko → name, symbol, price, volume_24h, FDV, homepage, description     |
| `geckoterminal.py` | GeckoTerminal → liquidity, GT Score, address, network                  |
| `dexscreener.py`   | Dexscreener → address, network, FDV, liquidity, volume_24h, pair_url     |

---

## 🧩 Function Reference

### fetch_token_stats_gecko(symbol: str) → dict
- name, symbol, price, volume_24h, fdv, homepage, description
- `source: "coingecko"`

### fetch_token_stats_terminal_by_address(network: str, address: str) → dict
- liq, gt_score
- `source: "geckoterminal"`

### fetch_token_stats_geckoterminal(symbol: str) → dict or list
- Combines GeckoTerminal token data with liquidity/GT score
- Useful for fuzzy matches

### fetch_token_from_geckoterminal_by_symbol(symbol: str) → dict or None
- Raw token object from GeckoTerminal token feed

### search_tokens_dexscreener(query: str) → List[dict]
- symbol, name, address, chain, dex, liquidity, volume, fdv, pair_url
- `source: "dexscreener"`

---

✅ Each function is standalone and ready to be reused in other projects.
✅ Imports are preserved via `__init__.py` for backward compatibility.