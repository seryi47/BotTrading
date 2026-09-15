"""Proveedor de noticias vía el RSS de búsqueda de Google News (público, sin
API key). Se usa para "vigilar" un tema (ej. una votación) igual que se
vigila un precio — no hay nivel que cruzar, pero sí "algo nuevo que avisar"."""

import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BotTrading/1.0)"}


def search(query, lang="es", country="ES", timeout=10):
    """Últimas noticias para `query`, más recientes primero (orden del feed).
    Cada resultado: {"title", "link", "source", "pub_date"}."""
    url = "https://news.google.com/rss/search?q=%s&hl=%s&gl=%s&ceid=%s:%s" % (
        quote(query), lang, country, country, lang)
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for item in root.findall(".//item"):
        source_el = item.find("source")
        out.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "source": source_el.text.strip() if source_el is not None and source_el.text else "",
            "pub_date": (item.findtext("pubDate") or "").strip(),
        })
    return out
