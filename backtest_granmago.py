#!/usr/bin/env python3
"""Backtest honesto de bottrading/granmago.py: recorta el histórico real a
cada "fecha pasada" (sin usar ni una vela del futuro respecto a ese punto —
el error clásico de backtest que invalidaría todo el resultado) y comprueba
si, de haber abierto el setup que el bot propuso ese día, el precio habría
tocado antes el stop loss o el take profit en las velas 4h siguientes.

Uso: python3 backtest_granmago.py [ETH|BTC] [--step N] [--horizon N]
"""

import sys

from bottrading import granmago
from bottrading.providers import binance

FORWARD_HORIZON = 90    # velas de 4h a mirar hacia delante (90*4h = 15 días)
MIN_LOOKBACK = 300      # velas de histórico que necesita compute_setup (ver granmago.py)


def slice_as_of(candles, as_of_ms):
    return [c for c in candles if c["open_time"] <= as_of_ms]


def outcome(h4_full, start_idx, direction, stop, tp, horizon=FORWARD_HORIZON):
    """Mira las velas 4h POSTERIORES a start_idx (sin incluir la que generó
    la señal) y dice qué tocó antes: 'tp' (gana), 'sl' (pierde), o 'ninguno'
    (no tocó ninguno de los dos dentro del horizonte)."""
    end = min(len(h4_full), start_idx + 1 + horizon)
    for c in h4_full[start_idx + 1:end]:
        if direction == "long":
            hit_sl = c["low"] <= stop
            hit_tp = c["high"] >= tp
        else:
            hit_sl = c["high"] >= stop
            hit_tp = c["low"] <= tp
        if hit_sl and hit_tp:
            return "ambos_misma_vela"  # vela con rango tan amplio que no se puede saber cuál fue primero
        if hit_sl:
            return "sl"
        if hit_tp:
            return "tp"
    return "ninguno"


def run(symbol, name, step=40, horizon=FORWARD_HORIZON):
    print("=== Backtest %s (step=%d velas de 4h, horizonte=%d velas) ===" % (name, step, horizon))
    weekly_full = binance.get_klines(symbol, "1w", 300)
    daily_full = binance.get_klines(symbol, "1d", 1000)
    h4_full = binance.get_klines_deep(symbol, "4h", 2500)
    print("Velas cargadas: semanal=%d, diario=%d, 4h=%d (desde %s hasta %s)" % (
        len(weekly_full), len(daily_full), len(h4_full),
        _fmt_ts(h4_full[0]["open_time"]), _fmt_ts(h4_full[-1]["open_time"])))

    results = []
    descartes = []
    i = MIN_LOOKBACK
    while i < len(h4_full) - horizon - 1:
        as_of_ms = h4_full[i]["open_time"]
        weekly = slice_as_of(weekly_full, as_of_ms)
        daily = slice_as_of(daily_full, as_of_ms)
        h4 = h4_full[:i + 1]  # incluye la vela i como "última cerrada" simulada

        if len(weekly) < 60 or len(daily) < 60:
            i += step
            continue

        setup = granmago.compute_setup(weekly, daily, h4, symbol, name)
        if setup["setup_valido"]:
            res = outcome(h4_full, i, setup["direction"], setup["stop_loss"], setup["take_profit"], horizon)
            results.append({"fecha": _fmt_ts(as_of_ms), "direccion": setup["direction"],
                            "precio": setup["price"], "stop": setup["stop_loss"],
                            "tp": setup["take_profit"], "resultado": res,
                            "rr": setup.get("riesgo_beneficio")})
        elif setup.get("sweep") and setup.get("confirmado"):
            # tenía barrido + confirmación pero se descartó por otra razón (normalmente R:R) — contarlo aparte
            descartes.append((_fmt_ts(as_of_ms), setup.get("direction"),
                              setup.get("riesgo_beneficio"), setup.get("motivo_descarte")))
        i += step

    print("\nSetups encontrados: %d" % len(results))
    for r in results:
        print("  %s | %s | precio %.2f | SL %.2f | TP %.2f -> %s" % (
            r["fecha"], r["direccion"], r["precio"], r["stop"], r["tp"], r["resultado"]))

    if results:
        tp = sum(1 for r in results if r["resultado"] == "tp")
        sl = sum(1 for r in results if r["resultado"] == "sl")
        ninguno = sum(1 for r in results if r["resultado"] == "ninguno")
        ambos = sum(1 for r in results if r["resultado"] == "ambos_misma_vela")
        decididos = tp + sl
        print("\nResumen: TP=%d  SL=%d  sin_resolver=%d  ambos_misma_vela(descartado)=%d" % (tp, sl, ninguno, ambos))
        if decididos:
            print("Win rate (sobre los resueltos): %.1f%%" % (100 * tp / decididos))
        total_r = sum((r["rr"] if r["resultado"] == "tp" else -1.0) for r in results if r["resultado"] in ("tp", "sl"))
        print("Expectativa total en R (unidades de riesgo arriesgado): %+.2f sobre %d operaciones resueltas" % (total_r, decididos))
    else:
        print("Ningún setup válido en todo el periodo con step=%d." % step)

    print("\nSetups con estructura+confirmación OK pero descartados (normalmente por R:R bajo): %d" % len(descartes))
    for fecha, direccion, rr, motivo in descartes[:15]:
        print("  %s | %s | R:R=%s | %s" % (fecha, direccion, ("%.2f" % rr) if rr is not None else "N/D", motivo))
    if len(descartes) > 15:
        print("  ... y %d más" % (len(descartes) - 15))
    return results


def _fmt_ts(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    args = sys.argv[1:]
    symbol = args[0].upper() if args and not args[0].startswith("--") else "ETH"
    step = 40
    horizon = FORWARD_HORIZON
    if "--step" in args:
        step = int(args[args.index("--step") + 1])
    if "--horizon" in args:
        horizon = int(args[args.index("--horizon") + 1])
    run(symbol, symbol, step=step, horizon=horizon)
