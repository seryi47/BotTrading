#!/usr/bin/env python3
"""BotTrading — modo CONFIG / NUBE.

  python run.py                 # vigilancia continua (local)
  python run.py --once          # una comprobación y sale
  python run.py --check         # una pasada tipo cron
  python run.py --loop          # bucle largo para GitHub Actions
  python run.py --test-telegram # envía un mensaje de prueba
  python run.py --chat-ids      # descubre chat ids (grupos incluidos)
"""

import os
import sys

import yaml

from bottrading.util_env import load_env
load_env()

from bottrading.engine import Engine
from bottrading.notifier import Notifier, chat_ids


def load_config(path=None):
    path = path or os.environ.get("BOTTRADING_CONFIG", "watches.yaml")
    if not os.path.exists(path):
        print("No existe %s. El repo ya trae uno con la watchlist inicial." % path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def main():
    cfg = load_config()
    chat_id = str(cfg.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
    notifier = Notifier(mac_alerts=bool(cfg.get("mac_alerts", True)))
    engine = Engine(
        notifier,
        poll_interval=int(cfg.get("poll_interval", 300)),
        default_chat_id=chat_id or None,
        digest_hour=int(cfg.get("digest_hour", 9)),
    )
    engine.seed_from_config(cfg.get("assets"))
    engine.set_paused(bool(cfg.get("paused", False)))

    if "--chat-ids" in sys.argv:
        from bottrading import commands
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            print("Falta TELEGRAM_BOT_TOKEN en el .env")
            return
        updates, _ = commands.get_updates(token, None, timeout=5)
        seen = {}
        for u in updates:
            msg = u.get("message") or u.get("edited_message") or {}
            ch = msg.get("chat") or {}
            if ch.get("id") is not None:
                seen[str(ch["id"])] = "%s — %s" % (ch.get("type", "?"),
                                                    ch.get("title") or ch.get("first_name") or "")
        if not seen:
            print("Sin mensajes recientes. Escribe algo al bot/grupo y reintenta.")
        for cid, desc in seen.items():
            print("  %-16s %s" % (cid, desc))
        return

    if "--test-telegram" in sys.argv:
        ok = notifier.telegram(chat_id, "✅ Prueba de <b>BotTrading</b>. Telegram funciona.")
        print("Telegram:", "ENVIADO" if ok else "FALLO (revisa token/chat_id)")
        return

    if "--check" in sys.argv:
        n = engine.check_once()
        print("Activos comprobados en esta pasada: %d" % n)
        return

    if "--loop" in sys.argv:
        import time as _t
        from bottrading import commands
        interval = int(os.environ.get("LOOP_INTERVAL", str(engine.poll_interval)))
        max_runtime = int(os.environ.get("MAX_RUNTIME_SECONDS", "20000"))
        handle_cmds = os.environ.get("HANDLE_COMMANDS", "0") == "1"
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        allowed = set(chat_ids(os.environ.get("TELEGRAM_CHAT_ID", "")))
        start = _t.time()
        last_check = 0.0
        offset = None
        print("Modo BUCLE: sondeo cada %ds, comandos=%s, máx %ds." % (interval, handle_cmds, max_runtime))
        while _t.time() - start < max_runtime:
            if _t.time() - last_check >= interval:
                try:
                    engine.tick()
                except Exception as e:
                    print("  error en pasada:", e)
                last_check = _t.time()

            if handle_cmds and token:
                try:
                    updates, offset = commands.get_updates(token, offset, timeout=20)
                    for u in updates:
                        msg = u.get("message") or u.get("edited_message") or {}
                        chat = str((msg.get("chat") or {}).get("id", ""))
                        if allowed and chat not in allowed:
                            continue
                        reply, _ch = commands.handle_text(msg.get("text", ""), chat, engine)
                        if reply:
                            notifier.telegram(chat, reply)
                    if engine.shutdown_requested:
                        print("  /apagar recibido, terminando bucle.")
                        break
                except Exception as e:
                    print("  error atendiendo comandos:", e)
            else:
                _t.sleep(max(1, min(interval, 20)))

            if _t.time() - start + 1 >= max_runtime:
                break
        print("Fin del bucle (relevo al siguiente run).")
        return

    print("=" * 64)
    print(" BotTrading — %d activos vigilados" % len(engine.assets))
    for a in engine.assets:
        print("  #%s %s (%s) — %d niveles" % (a["id"], a["symbol"], a["kind"], len(a["levels"])))
    print(" Telegram:", "OK" if (notifier.tg_token and chat_id) else "NO configurado")
    print("=" * 64)

    if "--once" in sys.argv:
        engine.tick()
        return

    try:
        engine.run_forever()
    except KeyboardInterrupt:
        print("\nParado por el usuario.")


if __name__ == "__main__":
    main()
