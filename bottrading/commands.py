"""Comandos de Telegram, compartidos por bot.py (local) y el bucle de Actions."""

import requests

from . import indicators as ind_mod
from .providers import crypto, stocks, fx


def ayuda():
    return (
        "📈 <b>BotTrading</b>\n\n"
        "Vigila BTC, ETH y unas cuantas acciones, y avisa en cuanto el precio "
        "cruza un nivel — con lectura técnica (RSI/medias), no solo el número.\n\n"
        "<b>Consultar</b>\n"
        "/lista — activos y niveles vigilados\n"
        "/precio SYMBOL — precio actual (ej. <code>/precio BTC</code>)\n"
        "/analisis SYMBOL [cripto|accion] — lectura técnica completa al momento\n"
        "/estado — ¿vigilando o en pausa?\n\n"
        "<b>Añadir un nivel</b> (campos separados por <code>;</code>):\n"
        "<code>/vigilar SYMBOL; cripto|accion; PRECIO; cae|sube; [nota]</code>\n"
        "Ejemplos:\n"
        "<code>/vigilar BTC; cripto; 69000; cae; soporte SMA200, zona de compra</code>\n"
        "<code>/vigilar ORCL; accion; 150; sube; rompe SMA50</code>\n"
        "<code>/borrar &lt;id_nivel&gt;</code> — quitar un nivel (el id sale en /lista)\n\n"
        "<b>Pararme</b>\n"
        "/pausa — dejo de vigilar y avisar (sigo aquí; <code>/seguir</code> para volver)\n"
        "/apagar si — me apago del todo\n"
    )


def _fmt_level(lv):
    flecha = "🔻cae a" if lv["direction"] == "cae" else "🚀sube a"
    nota = (" — %s" % lv["note"]) if lv.get("note") else ""
    return "   #%s %s %s%s" % (lv["id"], flecha, fx.fmt_usd_eur(lv["price"]), nota)


def _analisis_text(symbol, kind, source_id, name=None):
    provider = crypto if kind == "crypto" else stocks
    closes = provider.get_history(source_id)
    ind = ind_mod.read(closes)
    price = ind.price
    lines = [
        "🔎 <b>%s</b> — análisis técnico ahora mismo" % (name or symbol.upper()),
        "",
        "Precio: %s" % fx.fmt_usd_eur(price),
        "SMA20/50/200: %s / %s / %s" % tuple(
            fx.fmt_usd_eur(v) if v is not None else "—"
            for v in (ind.sma20, ind.sma50, ind.sma200)
        ),
        "RSI(14): %s" % ind.rsi_desc(),
        "Tendencia: %s" % ind.trend_desc(),
        "Rango 30d: %s — %s" % (fx.fmt_usd_eur(ind.low_30d), fx.fmt_usd_eur(ind.high_30d)),
    ]
    if ind.macd_hist is not None:
        lines.append("MACD hist.: %+.2f (%s)" % (ind.macd_hist, "ampliándose al alza" if ind.macd_hist > 0 else "a la baja"))
    return "\n".join(lines)


def handle_text(text, chat_id, engine):
    """Devuelve (respuesta:str|None, cambiada:bool)."""
    text = (text or "").strip()
    if not text.startswith("/"):
        return None, False
    cmd, _, rest = text.partition(" ")
    cmd = cmd.lstrip("/").lower().split("@")[0]
    rest = rest.strip()

    if cmd in ("start", "ayuda", "help"):
        return ayuda(), False

    if cmd == "lista":
        assets = engine.list_assets()
        if not assets:
            return "No hay activos vigilados todavía. Añade uno con /vigilar (mira /ayuda).", False
        lines = ["<b>Activos vigilados:</b>" if not engine.paused
                else "<b>Activos (⏸️ EN PAUSA — /seguir para reanudar):</b>"]
        for a in assets:
            lines.append("\n<b>%s</b> (%s)" % (a["name"], a["kind"]))
            if not a["levels"]:
                lines.append("   sin niveles")
            for lv in a["levels"]:
                lines.append(_fmt_level(lv))
        return "\n".join(lines), False

    if cmd == "precio":
        symbol = rest.strip()
        if not symbol:
            return "Uso: <code>/precio SYMBOL</code> (ej. <code>/precio BTC</code>)", False
        asset = engine.find_asset(symbol)
        try:
            if asset:
                price = engine.get_price(asset)
                return "%s: %s" % (asset["name"], fx.fmt_usd_eur(price)), False
            # no vigilado todavía: intenta cripto y si no, acción
            try:
                cid = crypto.resolve_id(symbol)
                price = crypto.get_price(cid)
            except Exception:
                price = stocks.get_price(symbol.upper())
            return "%s: %s" % (symbol.upper(), fx.fmt_usd_eur(price)), False
        except Exception as e:
            return "❌ No pude consultar '%s': %s" % (symbol, e), False

    if cmd == "analisis":
        parts = rest.split()
        if not parts:
            return "Uso: <code>/analisis SYMBOL [cripto|accion]</code>", False
        symbol = parts[0]
        kind_hint = parts[1].lower() if len(parts) > 1 else None
        asset = engine.find_asset(symbol)
        try:
            if asset:
                text_out = _analisis_text(asset["symbol"], asset["kind"], asset["source_id"], asset["name"])
            elif kind_hint in ("cripto", "crypto"):
                cid = crypto.resolve_id(symbol)
                text_out = _analisis_text(symbol, "crypto", cid)
            elif kind_hint in ("accion", "acción", "stock"):
                text_out = _analisis_text(symbol, "stock", symbol.upper())
            else:
                try:
                    cid = crypto.resolve_id(symbol)
                    text_out = _analisis_text(symbol, "crypto", cid)
                except Exception:
                    text_out = _analisis_text(symbol, "stock", symbol.upper())
            return text_out, False
        except Exception as e:
            return "❌ No pude analizar '%s': %s" % (symbol, e), False

    if cmd == "vigilar":
        parts = [p.strip() for p in rest.split(";")]
        if len(parts) < 4:
            return ("Formato:\n<code>/vigilar SYMBOL; cripto|accion; PRECIO; cae|sube; "
                    "[nota]</code>\n\nMira /ayuda para ejemplos."), False
        try:
            symbol, kind_raw, price_raw, dir_raw = parts[0], parts[1].lower(), parts[2], parts[3].lower()
            kind = "crypto" if kind_raw in ("cripto", "crypto") else "stock"
            price = float(price_raw.replace(",", "."))
            direction = "cae" if dir_raw in ("cae", "baja", "abajo") else "sube"
            note = parts[4] if len(parts) > 4 and parts[4] else ""
        except Exception as e:
            return "❌ Error: %s" % e, False
        try:
            asset, level = engine.add_level(symbol, kind, price, direction, note, chat_id=chat_id)
        except Exception as e:
            return "❌ No pude añadir el nivel: %s" % e, False
        return ("✅ Vigilando <b>#%s</b> en <b>%s</b>: aviso cuando %s %s\n%s" % (
            level["id"], asset["name"],
            "caiga a" if direction == "cae" else "supere",
            fx.fmt_usd_eur(price),
            ("📌 %s" % note) if note else "")), True

    if cmd == "borrar":
        if not rest.isdigit():
            return "Uso: <code>/borrar &lt;id_nivel&gt;</code> (mira /lista)", False
        ok = engine.remove_level(int(rest))
        return ("🗑️ Nivel #%s borrado" % rest if ok else "No encontré el nivel #%s" % rest), ok

    if cmd in ("pausa", "pausar", "parar", "stop"):
        if engine.paused:
            return "⏸️ Ya estaba en pausa. /seguir para reanudar.", False
        engine.set_paused(True)
        return "⏸️ <b>En pausa.</b> Dejo de consultar precios y de avisar. /seguir para reanudar.", True

    if cmd in ("seguir", "reanudar", "continuar"):
        if not engine.paused:
            return "▶️ Ya estaba vigilando.", False
        engine.set_paused(False)
        return "▶️ <b>Vigilando otra vez.</b>", True

    if cmd == "estado":
        assets = engine.list_assets()
        estado = "⏸️ en pausa" if engine.paused else "▶️ vigilando"
        return ("<b>Estado:</b> %s\nActivos: %d\nSondeo: cada %ds\n\n%s" % (
            estado, len(assets), engine.poll_interval,
            "/seguir para reanudar" if engine.paused else "/pausa para pararme")), False

    if cmd == "apagar":
        if rest.strip().lower() not in ("si", "sí", "confirmar"):
            return ("⚠️ <b>/apagar</b> me apaga del todo. Si solo quieres que deje de "
                    "avisarte, usa <b>/pausa</b> (esa sí se deshace con /seguir).\n\n"
                    "Para apagarme de verdad: <code>/apagar si</code>"), False
        engine.request_shutdown()
        return "🔌 <b>Apagándome.</b> Hasta luego.", False

    return "Comando no reconocido. Mira /ayuda.", False


def get_updates(token, offset=None, timeout=20):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params, timeout=timeout + 15)
    r.raise_for_status()
    data = r.json()
    updates = data.get("result", [])
    new_offset = offset
    for u in updates:
        new_offset = u["update_id"] + 1
    return updates, new_offset
