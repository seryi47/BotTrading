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


class Notifier:
    def __init__(self, tg_token=None, mac_alerts=True):
        self.tg_token = tg_token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.mac_alerts = mac_alerts

    def telegram(self, chat_id, text):
        ids = chat_ids(chat_id)
        if not self.tg_token or not ids:
            return False
        ok = True
        for cid in ids:
            ok = self._send_one(cid, text) and ok
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
