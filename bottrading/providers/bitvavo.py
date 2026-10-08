"""Proveedor de precio vía Bitvavo (API pública, sin key) — precio EUR
NATIVO del exchange donde el usuario tiene la posición real, para que el
informe de P&L no dependa de CoinGecko (en USD) + conversión con el tipo
de cambio cacheado de fx.py, que metía un ruido de ~0,1-0,15% frente al
precio real de Bitvavo."""

import requests

BASE = "https://api.bitvavo.com/v2"


def get_price(market):
    """market, p.ej. 'ETH-EUR'."""
    r = requests.get(f"{BASE}/ticker/price", params={"market": market}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "price" not in data:
        raise ValueError("Bitvavo no devolvió precio para '%s'" % market)
    return float(data["price"])
