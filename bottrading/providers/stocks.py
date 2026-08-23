"""Proveedor de precios de acciones vía el endpoint público de gráficos de
Yahoo Finance (sin key, sin librería adicional)."""

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BotTrading/1.0)"}


def _chart(ticker, range_="1y", interval="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    r = requests.get(url, params={"range": range_, "interval": interval},
                     headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    result = (data.get("chart") or {}).get("result")
    if not result:
        raise ValueError("Yahoo Finance no devolvió datos para '%s'" % ticker)
    result = result[0]
    quote = result["indicators"]["quote"][0]
    closes = [c for c in quote.get("close", []) if c is not None]
    return closes, result.get("meta", {})


def get_price(ticker):
    closes, meta = _chart(ticker, range_="5d", interval="1d")
    price = meta.get("regularMarketPrice")
    if price is None:
        if not closes:
            raise ValueError("Sin precio disponible para '%s'" % ticker)
        price = closes[-1]
    return float(price)


def get_history(ticker, days=252):
    closes, _meta = _chart(ticker, range_="1y", interval="1d")
    return closes[-days:] if len(closes) > days else closes
