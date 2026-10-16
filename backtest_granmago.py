#!/usr/bin/env python3
"""Backtest honesto de bottrading/granmago.py: recorta el histórico real a
cada "fecha pasada" (sin usar ni una vela del futuro respecto a ese punto —
el error clásico de backtest que invalidaría todo el resultado) y comprueba
si, de haber abierto el setup que el bot propuso ese día, el precio habría
tocado antes el stop loss o el take profit en las velas 4h siguientes.

Uso:
  python3 backtest_granmago.py ETH [--step N] [--horizon N]      # un activo
  python3 backtest_granmago.py --all [--step N] [--horizon N]    # cesta completa (BASKET)
"""

import sys
import time

from bottrading import granmago
from bottrading.providers import binance

FORWARD_HORIZON = 90    # velas de 4h a mirar hacia delante (90*4h = 15 días)
MIN_LOOKBACK = 300      # velas de histórico que necesita compute_setup (ver granmago.py)
MAX_4H_CANDLES = 30000  # tope alto: get_klines_deep para en cuanto Binance se queda sin histórico real

# Cesta de criptomonedas líquidas con histórico largo en Binance (comprobado
# el 16-oct-2026: todas tienen como mínimo ~6 años de velas de 4h, BTC/ETH
# ~9 años desde 2017-08-17) — para tener una muestra real de cientos de
# operaciones en vez de 17-18 de un único activo.
BASKET = ["BTC", "ETH", "BNB", "LTC", "XRP", "ADA", "TRX", "ETC", "XLM",
          "EOS", "LINK", "MATIC", "DOGE", "BCH", "SOL", "DOT", "AVAX"]


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


def run(symbol, name, step=40, horizon=FORWARD_HORIZON, verbose=True):
    if verbose:
        print("=== Backtest %s (step=%d velas de 4h, horizonte=%d velas) ===" % (name, step, horizon))
    weekly_full = binance.get_klines(symbol, "1w", 600)
    daily_full = binance.get_klines_deep(symbol, "1d", 5000)
    h4_full = binance.get_klines_deep(symbol, "4h", MAX_4H_CANDLES)
    if verbose:
        print("Velas cargadas: semanal=%d, diario=%d, 4h=%d (desde %s hasta %s)" % (
            len(weekly_full), len(daily_full), len(h4_full),
            _fmt_ts(h4_full[0]["open_time"]), _fmt_ts(h4_full[-1]["open_time"])))

    results = []
    descartes = []
    seen_sweeps = set()  # (idx del barrido) ya contado — SIN esto, el mismo barrido real se
    # cuenta como varias "operaciones" distintas mientras sigue confirmado en los sucesivos
    # sondeos (verificado el 16-oct-2026: con step pequeño salían el doble/triple de "setups"
    # que con step grande, puro artefacto de recuento, no más oportunidades reales). El bot en
    # vivo ya deduplica así (ver Engine._granmago_last_sweep) — el backtest tiene que hacer lo mismo.
    i = MIN_LOOKBACK
    while i < len(h4_full) - horizon - 1:
        as_of_ms = h4_full[i]["open_time"]
        weekly = slice_as_of(weekly_full, as_of_ms)
        daily = slice_as_of(daily_full, as_of_ms)
        h4 = h4_full[:i + 1]  # incluye la vela i como "última cerrada" simulada

        if len(weekly) < 60 or len(daily) < 60:
            i += step
            continue

        try:
            setup = granmago.compute_setup(weekly, daily, h4, symbol, name)
        except Exception as e:
            print("  [%s] error en compute_setup a %s: %s" % (symbol, _fmt_ts(as_of_ms), e))
            i += step
            continue
        if setup["setup_valido"]:
            sweep_idx = setup["sweep"]["idx"]
            if sweep_idx in seen_sweeps:
                i += step
                continue
            seen_sweeps.add(sweep_idx)
            res = outcome(h4_full, i, setup["direction"], setup["stop_loss"], setup["take_profit"], horizon)
            results.append({"symbol": symbol, "fecha": _fmt_ts(as_of_ms), "direccion": setup["direction"],
                            "precio": setup["price"], "stop": setup["stop_loss"],
                            "tp": setup["take_profit"], "resultado": res,
                            "rr": setup.get("riesgo_beneficio")})
        elif setup.get("sweep") and setup.get("confirmado"):
            descartes.append((_fmt_ts(as_of_ms), setup.get("direction"),
                              setup.get("riesgo_beneficio"), setup.get("motivo_descarte")))
        i += step

    if verbose:
        _print_summary(name, results, descartes)
    return results, descartes


def _print_summary(name, results, descartes):
    print("\nSetups encontrados (%s): %d" % (name, len(results)))
    if results:
        tp = sum(1 for r in results if r["resultado"] == "tp")
        sl = sum(1 for r in results if r["resultado"] == "sl")
        ninguno = sum(1 for r in results if r["resultado"] == "ninguno")
        ambos = sum(1 for r in results if r["resultado"] == "ambos_misma_vela")
        decididos = tp + sl
        print("Resumen: TP=%d  SL=%d  sin_resolver=%d  ambos_misma_vela(descartado)=%d" % (tp, sl, ninguno, ambos))
        if decididos:
            print("Win rate (sobre los resueltos): %.1f%%" % (100 * tp / decididos))
        total_r = sum((r["rr"] if r["resultado"] == "tp" else -1.0) for r in results if r["resultado"] in ("tp", "sl"))
        print("Expectativa total en R: %+.2f sobre %d operaciones resueltas" % (total_r, decididos))
    print("Descartados por R:R bajo u otra razón (estructura+confirmación OK): %d" % len(descartes))


def run_basket(basket=BASKET, step=40, horizon=FORWARD_HORIZON):
    all_results, all_descartes = [], []
    for i, symbol in enumerate(basket):
        if i > 0:
            time.sleep(1.0)
        print("\n--- %s (%d/%d) ---" % (symbol, i + 1, len(basket)))
        try:
            results, descartes = run(symbol, symbol, step=step, horizon=horizon, verbose=False)
        except Exception as e:
            print("  ERROR con %s: %s — se omite este activo" % (symbol, e))
            continue
        tp = sum(1 for r in results if r["resultado"] == "tp")
        sl = sum(1 for r in results if r["resultado"] == "sl")
        print("  setups=%d  TP=%d  SL=%d  (resto sin resolver/ambos)" % (len(results), tp, sl))
        all_results.extend(results)
        all_descartes.extend(descartes)

    print("\n" + "=" * 70)
    print("RESUMEN AGREGADO — %d activos, step=%d, horizonte=%d velas" % (len(basket), step, horizon))
    print("=" * 70)
    _print_summary("TODOS LOS ACTIVOS", all_results, all_descartes)

    print("\nDesglose por activo:")
    by_symbol = {}
    for r in all_results:
        by_symbol.setdefault(r["symbol"], []).append(r)
    for sym, rs in sorted(by_symbol.items()):
        tp = sum(1 for r in rs if r["resultado"] == "tp")
        sl = sum(1 for r in rs if r["resultado"] == "sl")
        decididos = tp + sl
        total_r = sum((r["rr"] if r["resultado"] == "tp" else -1.0) for r in rs if r["resultado"] in ("tp", "sl"))
        wr = (100 * tp / decididos) if decididos else 0.0
        print("  %-6s setups=%3d  TP=%3d  SL=%3d  win_rate=%5.1f%%  expectativa=%+6.2fR" % (
            sym, len(rs), tp, sl, wr, total_r))
    return all_results, all_descartes


def _fmt_ts(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    args = sys.argv[1:]
    step = 40
    horizon = FORWARD_HORIZON
    if "--step" in args:
        step = int(args[args.index("--step") + 1])
    if "--horizon" in args:
        horizon = int(args[args.index("--horizon") + 1])
    if "--all" in args:
        run_basket(step=step, horizon=horizon)
    else:
        symbol = args[0].upper() if args and not args[0].startswith("--") else "ETH"
        run(symbol, symbol, step=step, horizon=horizon)
