"""Proveedor de precios cripto vía CoinGecko (API pública, sin key)."""

import time

import requests

BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "BotTrading/1.0"}


def _get(url, params, timeout):
    """GET con un reintento si CoinGecko rate-limita (429) en ráfaga."""
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    if r.status_code == 429:
        time.sleep(5)
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r

# Atajos para no tener que escribir el id de CoinGecko cada vez.
COMMON_IDS = {
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "eth": "ethereum", "ethereum": "ethereum",
    "sol": "solana", "solana": "solana",
    "xrp": "ripple", "ripple": "ripple",
    "ada": "cardano", "cardano": "cardano",
    "bnb": "binancecoin",
    "doge": "dogecoin", "dogecoin": "dogecoin",
}


def resolve_id(symbol):
    """Convierte un ticker/nombre común a id de CoinGecko. Si no lo conoce,
    pregunta al buscador de CoinGecko y coge el primer resultado."""
    key = symbol.strip().lower()
    if key in COMMON_IDS:
        return COMMON_IDS[key]
    r = _get(f"{BASE}/search", {"query": symbol}, 20)
    coins = r.json().get("coins") or []
    if not coins:
        raise ValueError("No encuentro ninguna cripto que se llame '%s'" % symbol)
    return coins[0]["id"]


def get_price(coingecko_id):
    r = _get(f"{BASE}/simple/price", {"ids": coingecko_id, "vs_currencies": "usd"}, 20)
    data = r.json()
    if coingecko_id not in data:
        raise ValueError("CoinGecko no devolvió precio para '%s'" % coingecko_id)
    return float(data[coingecko_id]["usd"])


def get_history(coingecko_id, days=210):
    r = _get(f"{BASE}/coins/{coingecko_id}/market_chart",
            {"vs_currency": "usd", "days": days, "interval": "daily"}, 30)
    prices = r.json().get("prices") or []
    return [p[1] for p in prices if p[1] is not None]
