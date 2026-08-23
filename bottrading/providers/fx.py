"""Tipo de cambio USD→EUR (para mostrar los precios en euros, como prefiere
el usuario). El mercado real cotiza en USD; esto es solo una conversión para
que se lea cómodo — ver aviso en README."""

import time

import requests

_cache = {"rate": 0.86, "ts": 0.0}   # valor de respaldo razonable si la API falla
TTL_SECONDS = 3600


def usd_to_eur():
    now = time.time()
    if now - _cache["ts"] < TTL_SECONDS:
        return _cache["rate"]
    try:
        r = requests.get("https://api.frankfurter.app/latest",
                         params={"from": "USD", "to": "EUR"}, timeout=10)
        r.raise_for_status()
        rate = float(r.json()["rates"]["EUR"])
        _cache["rate"], _cache["ts"] = rate, now
    except Exception as e:
        print("[fx] no pude actualizar el tipo de cambio, uso el último conocido:", e)
    return _cache["rate"]


def fmt_usd_eur(value_usd):
    eur = value_usd * usd_to_eur()
    return "$%s (%s €)" % (_fmt(value_usd), _fmt(eur))


def _fmt(n):
    return "{:,.2f}".format(n).replace(",", "@").replace(".", ",").replace("@", ".")
