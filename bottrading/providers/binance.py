"""Velas OHLC vía Binance (API pública, sin key) — necesarias para la
metodología GranMago (bottrading/granmago.py), que opera en semanal/diario/4h
con máximos/mínimos y mechas reales. CoinGecko (crypto.py) solo da precio
puntual y cierres diarios, no sirve para estructura de velas."""

import requests

BASE = "https://api.binance.com/api/v3"

# Atajos de símbolo a par de Binance (USDT) — ampliar si se añaden más activos.
SYMBOLS = {
    "ETH": "ETHUSDT", "ethereum": "ETHUSDT",
    "BTC": "BTCUSDT", "bitcoin": "BTCUSDT",
}


def resolve_symbol(name):
    return SYMBOLS.get(name, SYMBOLS.get(name.upper(), name.upper() + "USDT"))


def get_klines(symbol, interval, limit=300):
    """symbol: p.ej. 'ETHUSDT' (o una clave de SYMBOLS). interval: '1w'/'1d'/'4h'.
    Devuelve lista cronológica de dicts (el último es la vela más reciente,
    OJO: Binance incluye la vela EN CURSO sin cerrar como último elemento)."""
    pair = resolve_symbol(symbol)
    r = requests.get(f"{BASE}/klines",
                     params={"symbol": pair, "interval": interval, "limit": limit},
                     timeout=20)
    r.raise_for_status()
    rows = r.json()
    return [
        {"open_time": row[0], "open": float(row[1]), "high": float(row[2]),
         "low": float(row[3]), "close": float(row[4]), "close_time": row[6]}
        for row in rows
    ]


def get_klines_deep(symbol, interval, total):
    """Como get_klines pero paginando hacia atrás en el tiempo para traer más
    de las 1000 velas máximas por petición de Binance — lo usa el backtest
    (bottrading/backtest_granmago.py), que necesita cientos de días de
    histórico de 4h para tener suficientes puntos de prueba independientes."""
    pair = resolve_symbol(symbol)
    out = []
    end_time = None
    while len(out) < total:
        batch = min(1000, total - len(out))
        params = {"symbol": pair, "interval": interval, "limit": batch}
        if end_time is not None:
            params["endTime"] = end_time
        r = requests.get(f"{BASE}/klines", params=params, timeout=20)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        chunk = [
            {"open_time": row[0], "open": float(row[1]), "high": float(row[2]),
             "low": float(row[3]), "close": float(row[4]), "close_time": row[6]}
            for row in rows
        ]
        out = chunk + out
        end_time = chunk[0]["open_time"] - 1
        if len(rows) < batch:
            break  # no hay más histórico disponible
    return out
