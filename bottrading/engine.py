"""Motor de vigilancia: sondea precios, detecta cruces de nivel y manda avisos
con lectura técnica (RSI/MACD/medias), igual que hemos ido razonando a mano en
el chat. Misma filosofía que el motor de BotViajes, adaptada a precios."""

import json
import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import indicators as ind_mod
from .providers import crypto, stocks, fx

MADRID = ZoneInfo("Europe/Madrid")


class Engine:
    def __init__(self, notifier, poll_interval=300, default_chat_id=None,
                 state_file="watches.json", history_ttl=14400, digest_hour=9,
                 digest_state_file=None):
        self.notifier = notifier
        self.poll_interval = poll_interval      # cada cuánto se consulta precio (s)
        self.default_chat_id = default_chat_id
        self.state_file = state_file
        self.history_ttl = history_ttl          # cada cuánto se refresca el histórico (s)
        self.digest_hour = digest_hour           # hora (Europe/Madrid) del resumen diario
        # Archivo aparte para "ya mandé el resumen de hoy" (sin datos personales),
        # pensado para poder commitearse a un repo PÚBLICO en modo nube: en
        # GitHub Actions cada relevo del job arranca de cero y, sin esto, el
        # resumen diario se repetiría en cada relevo posterior a digest_hour.
        self.digest_state_file = digest_state_file
        self._lock = threading.RLock()
        self.assets = []                        # persistente: lista de dicts
        self.paused = False
        self.last_digest_date = None
        self.digest_just_sent = False           # runtime: para que run.py sepa si debe commitear
        self.shutdown_requested = False
        self._stop = threading.Event()
        self._ind_cache = {}                    # runtime: {asset_id: {"ts", "ind"}}
        self._load()

    # ---- persistencia --------------------------------------------------
    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self.assets = data.get("assets", [])
                self.paused = bool(data.get("paused", False))
                self.last_digest_date = data.get("last_digest_date")
            except Exception as e:
                print("[engine] no se pudo leer %s: %s" % (self.state_file, e))
        if self.digest_state_file and os.path.exists(self.digest_state_file):
            try:
                with open(self.digest_state_file, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                # el archivo compartido (git) manda si es igual o más reciente
                if d.get("last_digest_date"):
                    self.last_digest_date = d["last_digest_date"]
            except Exception as e:
                print("[engine] no se pudo leer %s: %s" % (self.digest_state_file, e))

    def _save(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as fh:
                json.dump({"assets": self.assets, "paused": self.paused,
                          "last_digest_date": self.last_digest_date},
                         fh, ensure_ascii=False, indent=2)
        except Exception as e:
            print("[engine] no se pudo guardar %s: %s" % (self.state_file, e))
        if self.digest_state_file:
            try:
                os.makedirs(os.path.dirname(self.digest_state_file) or ".", exist_ok=True)
                with open(self.digest_state_file, "w", encoding="utf-8") as fh:
                    json.dump({"last_digest_date": self.last_digest_date}, fh)
            except Exception as e:
                print("[engine] no se pudo guardar %s: %s" % (self.digest_state_file, e))

    # ---- gestión de activos y niveles -----------------------------------
    def _next_asset_id(self):
        return (max([a["id"] for a in self.assets], default=0) + 1)

    def _next_level_id(self):
        ids = [lv["id"] for a in self.assets for lv in a["levels"]]
        return (max(ids, default=0) + 1)

    def find_asset(self, symbol):
        symbol = symbol.strip().upper()
        for a in self.assets:
            if a["symbol"].upper() == symbol:
                return a
        return None

    def add_asset(self, symbol, kind, source_id, name=None):
        with self._lock:
            a = {"id": self._next_asset_id(), "symbol": symbol.upper(), "kind": kind,
                "source_id": source_id, "name": name or symbol.upper(),
                "levels": [], "chat_id": None, "enabled": True, "last_price": None}
            self.assets.append(a)
            self._save()
            return a

    def add_level(self, symbol, kind, price, direction, note="", chat_id=None, source_id=None, ma=None):
        """Añade un nivel a un activo; crea el activo si no existía todavía.
        Un nivel es o bien un precio fijo (`price`) o una media en vivo (`ma`
        = "sma20"|"sma50"|"sma200") que se recalcula sola en cada sondeo."""
        with self._lock:
            asset = self.find_asset(symbol)
            if asset is None:
                if source_id is None:
                    if kind == "crypto":
                        source_id = crypto.resolve_id(symbol)
                    else:
                        source_id = symbol.upper()
                asset = self.add_asset(symbol, kind, source_id)
            level = {"id": self._next_level_id(), "direction": direction, "note": note,
                    "created_by": str(chat_id) if chat_id else "config"}
            if ma:
                level["ma"] = ma
            else:
                level["price"] = float(price)
            asset["levels"].append(level)
            if chat_id:
                asset["chat_id"] = str(chat_id)
            self._save()
            return asset, level

    def remove_level(self, level_id):
        with self._lock:
            for a in self.assets:
                before = len(a["levels"])
                a["levels"] = [lv for lv in a["levels"] if lv["id"] != int(level_id)]
                if len(a["levels"]) < before:
                    self._save()
                    return True
            return False

    def seed_from_config(self, config_assets):
        """Carga los activos definidos en watches.yaml sin duplicar por símbolo."""
        with self._lock:
            for ca in (config_assets or []):
                symbol = ca["symbol"].upper()
                asset = self.find_asset(symbol)
                if asset is None:
                    asset = self.add_asset(symbol, ca["kind"], ca["source_id"], ca.get("name"))
                def dedup_key(lv):
                    return (lv["direction"], lv.get("ma") or round(float(lv["price"]), 2))
                existing = {dedup_key(lv) for lv in asset["levels"]}
                for lv in ca.get("levels", []):
                    key = dedup_key(lv)
                    if key in existing:
                        continue
                    new_lv = {"id": self._next_level_id(), "direction": lv["direction"],
                             "note": lv.get("note", ""), "created_by": "config"}
                    if lv.get("ma"):
                        new_lv["ma"] = lv["ma"]
                    else:
                        new_lv["price"] = float(lv["price"])
                    asset["levels"].append(new_lv)
            self._save()

    def list_assets(self):
        with self._lock:
            return list(self.assets)

    def set_paused(self, value):
        with self._lock:
            self.paused = bool(value)
            self._save()
            return self.paused

    def request_shutdown(self):
        self.shutdown_requested = True
        self._stop.set()

    # ---- precios e indicadores ------------------------------------------
    def _provider_for(self, asset):
        return crypto if asset["kind"] == "crypto" else stocks

    def get_price(self, asset):
        return self._provider_for(asset).get_price(asset["source_id"])

    def get_indicators(self, asset, force=False):
        """Snapshot técnico con caché (no hace falta recalcular en cada tick)."""
        cached = self._ind_cache.get(asset["id"])
        now = time.time()
        if not force and cached and now - cached["ts"] < self.history_ttl:
            return cached["ind"]
        try:
            closes = self._provider_for(asset).get_history(asset["source_id"])
            snapshot = ind_mod.read(closes)
        except Exception as e:
            print("  [%s] no pude calcular indicadores: %s" % (asset["symbol"], e))
            snapshot = cached["ind"] if cached else None
        self._ind_cache[asset["id"]] = {"ts": now, "ind": snapshot}
        return snapshot

    # ---- avisos -----------------------------------------------------------
    def _chat_for(self, asset):
        return asset.get("chat_id") or self.default_chat_id

    def _level_alert_text(self, asset, level, target, price, ind):
        arrow = "🔻" if level["direction"] == "cae" else "🚀"
        tag = ind_mod.classify_alert(level["direction"], ind) if ind else "🟡 Sin lectura técnica disponible"
        etiqueta = (" (%s)" % level["ma"].upper()) if level.get("ma") else ""
        lines = [
            "%s <b>%s</b> ha %s <b>%s</b>%s" % (
                arrow, asset["name"],
                "caído a" if level["direction"] == "cae" else "superado",
                fx.fmt_usd_eur(target), etiqueta),
            "Precio actual: %s" % fx.fmt_usd_eur(price),
        ]
        if level.get("note"):
            lines.append("📌 %s" % level["note"])
        if ind:
            lines += [
                "",
                "RSI(14): %s" % ind.rsi_desc(),
                "Tendencia: %s" % ind.trend_desc(),
            ]
        lines += ["", tag]
        return "\n".join(lines)

    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    @staticmethod
    def _pct(a, b):
        return ("%+.1f" % ((a / b - 1) * 100)).replace(".", ",")

    def _digest_text(self):
        now = datetime.now(MADRID)
        fecha = "%d de %s, %02d:%02d" % (now.day, self.MESES[now.month - 1], now.hour, now.minute)
        lines = [
            "📊 <b>BotTrading</b> — resumen de hoy",
            "🗓 %s (hora de Madrid)" % fecha,
            "🟢 entra · 🟠 cuidado · 🟡 neutral · 🔴 no compres · ⚪ sin datos",
        ]
        for i, asset in enumerate(self.assets):
            if i > 0:
                time.sleep(1.2)
            try:
                price = self.get_price(asset)
            except Exception as e:
                lines.append("\n⚪ <b>%s</b> — no pude consultar el precio (%s)" % (asset["name"], e))
                continue
            ind = self.get_indicators(asset)
            emoji, motivo = ind_mod.overall_signal(ind)
            # resuelve cada nivel (fijo o "ma") a su precio vivo antes de buscar
            # el más cercano — si no hay indicador todavía, los niveles "ma" se
            # descartan de esta pasada (no se puede saber dónde está la SMA)
            resolved = []
            for lv in asset["levels"]:
                target = ind_mod.resolve_level_price(lv, ind)
                if target is not None:
                    resolved.append({**lv, "price": target})
            support, resistance = ind_mod.nearest_levels(price, resolved)

            card = ["%s <b>%s</b> · %s" % (emoji, asset["name"], asset["symbol"]),
                   "<code>%s</code>" % fx.fmt_usd_eur(price)]
            if ind and ind.rsi14 is not None:
                card.append("RSI %.0f · %s" % (ind.rsi14, ind.trend_desc()))
            loc = []
            if support:
                loc.append("Soporte %s (%s%%)" % (fx.fmt_usd_eur(support["price"]), self._pct(support["price"], price)))
            if resistance:
                loc.append("Resistencia %s (%s%%)" % (fx.fmt_usd_eur(resistance["price"]), self._pct(resistance["price"], price)))
            if loc:
                card.append("📍 " + " · ".join(loc))
            card.append("")
            card.append("🚦 <b>Ahora:</b> %s" % motivo)
            plan = ind_mod.buy_plan(ind.rsi14 if ind else None, support, resistance, fx.fmt_usd_eur)
            card.append("🎯 <b>Compraría si:</b> %s" % plan)
            if support and support.get("note"):
                card.append("<i>%s</i>" % support["note"])
            lines.append("\n<blockquote>%s</blockquote>" % "\n".join(card))
        return "\n".join(lines)

    def _maybe_send_digest(self):
        self.digest_just_sent = False
        now = datetime.now(MADRID)
        today = now.strftime("%Y-%m-%d")
        if now.hour < self.digest_hour or self.last_digest_date == today:
            return
        if not self.assets:
            return
        self.notifier.telegram(self.default_chat_id, self._digest_text())
        self.last_digest_date = today
        self.digest_just_sent = True
        self._save()

    # ---- bucle --------------------------------------------------------------
    def tick(self):
        if self.paused:
            return
        with self._lock:
            assets = list(self.assets)
        for i, asset in enumerate(assets):
            if not asset.get("enabled", True):
                continue
            if i > 0:
                time.sleep(1.2)  # no machacar las APIs gratuitas (CoinGecko rate-limita en ráfaga)
            try:
                price = self.get_price(asset)
            except Exception as e:
                print("  [%s] error al consultar precio: %s" % (asset["symbol"], e))
                continue
            prev = asset.get("last_price")
            # las medias (SMA20/50/200) hay que resolverlas en vivo, no cachearlas
            # como precio fijo — si el activo tiene algún nivel "ma", nos hace
            # falta el indicador ya en esta pasada, no solo al disparar el aviso
            needs_ind = any(lv.get("ma") for lv in asset["levels"])
            ind_now = self.get_indicators(asset) if needs_ind else None
            fired = []
            if prev is not None:
                for lv in asset["levels"]:
                    target = ind_mod.resolve_level_price(lv, ind_now)
                    if target is None:
                        continue
                    if lv["direction"] == "cae" and prev > target >= price:
                        fired.append((lv, target))
                    elif lv["direction"] == "sube" and prev < target <= price:
                        fired.append((lv, target))
            asset["last_price"] = price
            if fired:
                ind = self.get_indicators(asset, force=True)
                chat = self._chat_for(asset)
                for lv, target in fired:
                    self.notifier.telegram(chat, self._level_alert_text(asset, lv, target, price, ind))
                    self.notifier.mac("BotTrading", "%s cruzó %s" % (asset["symbol"], target))
            stamp = time.strftime("%H:%M:%S")
            print("[%s] %s -> %s%s" % (stamp, asset["symbol"], price,
                                       "  (%d aviso/s)" % len(fired) if fired else ""))
        self._save()
        self._maybe_send_digest()

    def check_once(self):
        if self.paused:
            print("[%s] en pausa (/seguir para reanudar)" % time.strftime("%H:%M:%S"))
            return 0
        self.tick()
        return len(self.assets)

    def run_forever(self):
        print("[engine] vigilando %d activos | sondeo cada %ds" %
              (len(self.assets), self.poll_interval))
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as e:
                print("[engine] error en tick:", e)
            self._stop.wait(self.poll_interval)

    def start_background(self):
        t = threading.Thread(target=self.run_forever, daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop.set()
