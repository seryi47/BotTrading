"""Velas OHLC vía Kraken (API pública, sin key) — para el bot EN VIVO.

Binance bloquea con HTTP 451 ("Unavailable For Legal Reasons") las
peticiones desde los servidores de GitHub Actions (datacenters en EEUU) —
confirmado el 19-oct-2026: el chequeo de Turtle llevaba 3 días fallando en
silencio por esto, aunque funcionaba perfecto en pruebas locales. Kraken,
al ser un exchange con sede en EEUU, no bloquea esas IPs.

Limitación real de Kraken (a cambio): el endpoint público de OHLC no pagina
hacia atrás, da como mucho ~720 velas por petición — de sobra para uso en
vivo (el sistema Turtle necesita como mucho ~150-200 días de histórico),
pero NO sirve para repetir el backtest de 9 años (eso se sigue haciendo con
Binance desde una máquina local, donde no hay bloqueo — ver
backtest_turtle.py, que no corre nunca en GitHub Actions)."""

import requests

BASE = "https://api.kraken.com/0/public"

PAIRS = {
    "ETH": "ETHUSD", "ethereum": "ETHUSD",
    "BTC": "XBTUSD", "bitcoin": "XBTUSD",
}

INTERVALS = {"1w": 10080, "1d": 1440, "4h": 240}


def resolve_pair(name):
    return PAIRS.get(name, PAIRS.get(name.upper(), name.upper() + "USD"))


def get_klines(symbol, interval, limit=None):
    """interval: '1w'/'1d'/'4h'. Devuelve lista cronológica de dicts
    (open_time en ms, como binance.py, para que el resto del código no
    tenga que distinguir el proveedor) — el último elemento es la vela EN
    CURSO, sin cerrar, igual que en Binance."""
    pair = resolve_pair(symbol)
    minutes = INTERVALS[interval]
    r = requests.get(f"{BASE}/OHLC", params={"pair": pair, "interval": minutes}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise ValueError("Kraken error para %s: %s" % (pair, data["error"]))
    key = next(k for k in data["result"].keys() if k != "last")
    rows = data["result"][key]
    out = [
        {"open_time": row[0] * 1000, "open": float(row[1]), "high": float(row[2]),
         "low": float(row[3]), "close": float(row[4]), "close_time": (row[0] + minutes * 60) * 1000}
        for row in rows
    ]
    return out[-limit:] if limit else out
