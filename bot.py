#!/usr/bin/env python3
"""BotTrading — modo BOT interactivo de Telegram (para una máquina propia).

Arranca el motor de vigilancia en segundo plano y escucha comandos de Telegram
por long-polling.

  python bot.py
"""

import os

from bottrading.util_env import load_env
load_env()

import telebot
import yaml

from bottrading import commands
from bottrading.engine import Engine
from bottrading.notifier import Notifier

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("Falta TELEGRAM_BOT_TOKEN en el .env")

POLL = int(os.environ.get("POLL_INTERVAL", "300"))

notifier = Notifier(tg_token=TOKEN, mac_alerts=os.environ.get("MAC_ALERTS", "1") == "1")
engine = Engine(notifier, poll_interval=POLL,
                default_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None)

try:
    if os.path.exists("watches.yaml"):
        with open("watches.yaml", "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}
        engine.seed_from_config(cfg.get("assets"))
except Exception as e:
    print("[bot] aviso al leer watches.yaml:", e)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


@bot.message_handler(func=lambda m: True)
def _any(m):
    reply, _changed = commands.handle_text(m.text, m.chat.id, engine)
    if reply:
        bot.reply_to(m, reply)


def main():
    engine.start_background()
    print("[bot] en marcha. Escríbele /start en Telegram.")
    bot.infinity_polling(skip_pending=True, timeout=30)


if __name__ == "__main__":
    main()
