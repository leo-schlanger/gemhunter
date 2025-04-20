import requests

def try_dexscreener_network(network):
    url = f"https://api.dexscreener.com/latest/dex/pairs/{network}"
    try:
        response = requests.get(url, timeout=10)
        print(f"🔹 {network} — {response.status_code}")
        if response.status_code == 200:
            data = response.json().get("pairs", [])
            print(f"   ➝ {len(data)} pairs")
        else:
            print("   ❌ Not available or blocked.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

# Test networks
networks = ["ethereum", "bsc", "polygon", "solana", "base", "arbitrum", "optimism", "avax", "fantom", "sonic", "sui", "berachain", "monad"]

for net in networks:
    try_dexscreener_network(net)
