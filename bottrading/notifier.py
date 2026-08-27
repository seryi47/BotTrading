"""Avisos por Telegram (+ opcional notificación de Mac)."""

import os
import re
import subprocess
import sys

import requests

IS_MAC = sys.platform == "darwin"


def chat_ids(value):
    """Normaliza un destino de Telegram a lista de chat ids (admite varios
    separados por coma/espacio; los grupos tienen id negativo)."""
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else re.split(r"[,\s]+", str(value))
    return [str(i).strip() for i in items if str(i).strip()]


TELEGRAM_MAX_LEN = 3000  # margen AMPLIO bajo el límite real (4096): mientras
# una tarjeta está "abierta" (dentro de un <blockquote>) no se puede cortar
# sin romper el HTML, así que el trozo puede crecer una tarjeta entera más
# allá de este umbral antes de encontrar el siguiente punto seguro — dejar
# ~1000 caracteres de colchón evita que esa tarjeta de propina se pase de 4096.


def split_message(text, max_len=TELEGRAM_MAX_LEN):
    """Parte un mensaje largo en trozos que quepan en un mensaje de Telegram.
    NUNCA corta mientras haya un <blockquote> abierto sin cerrar — el
    resumen diario mete una línea en blanco dentro de cada tarjeta (antes de
    "Ahora:"), así que partir por "línea en blanco" a secas rompía el HTML a
    mitad de etiqueta. Corte PROACTIVO: en cuanto se vuelve a un punto seguro
    (balance de <blockquote> a cero) habiendo ya alcanzado max_len, se corta
    ahí — no se espera a que la siguiente línea desborde, porque para entonces
    ya podría ser demasiado tarde para cortar sin romper una etiqueta."""
    if len(text) <= max_len:
        return [text]
    lines = text.split("\n")
    parts, current, depth = [], "", 0
    for line in lines:
        current = (current + "\n" + line) if current else line
        depth += line.count("<blockquote") - line.count("</blockquote>")
        if depth == 0 and len(current) >= max_len:
            parts.append(current)
            current = ""
    if current:
        parts.append(current)
    return parts


class Notifier:
    def __init__(self, tg_token=None, mac_alerts=True):
        self.tg_token = tg_token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.mac_alerts = mac_alerts

    def telegram(self, chat_id, text):
        ids = chat_ids(chat_id)
        if not self.tg_token or not ids:
            return False
        chunks = split_message(text)
        ok = True
        for cid in ids:
            for i, chunk in enumerate(chunks):
                if len(chunks) > 1:
                    chunk = "%s\n\n<i>(%d/%d)</i>" % (chunk, i + 1, len(chunks))
                ok = self._send_one(cid, chunk) and ok
        return ok

    def _send_one(self, chat_id, text):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{self.tg_token}/sendMessage",
                data={"chat_id": str(chat_id), "text": text, "parse_mode": "HTML",
                     "disable_web_page_preview": "true"},
                timeout=20,
            )
            if not r.ok:
                print("  [telegram] %s: %s" % (r.status_code, r.text[:200]))
            return r.ok
        except Exception as e:
            print("  [telegram] error:", e)
            return False

    def mac(self, title, message):
        if not self.mac_alerts or not IS_MAC:
            return
        try:
            subprocess.run(
                ["osascript", "-e",
                 'display notification %r with title %r sound name "Glass"' % (message, title)],
                check=False,
            )
        except Exception as e:
            print("  [mac] error:", e)
