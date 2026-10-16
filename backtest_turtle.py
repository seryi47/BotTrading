#!/usr/bin/env python3
"""Backtest de los sistemas Turtle Traders (bottrading/turtle.py) sobre
velas DIARIAS reales (máximo histórico disponible en Binance). Igual de
honesto que backtest_granmago.py: recorre las velas en orden sin mirar al
futuro, un solo activo a la vez.

Uso: python3 backtest_turtle.py [ETH|BTC|--all]
"""

import sys

from bottrading import turtle
from bottrading.providers import binance

BASKET = ["BTC", "ETH", "BNB", "LTC", "XRP", "ADA", "TRX", "ETC", "XLM",
          "EOS", "LINK", "MATIC", "DOGE", "BCH", "SOL", "DOT", "AVAX"]


def run(symbol):
    daily = binance.get_klines_deep(symbol, "1d", 5000)
    print("%s: %d velas diarias (%s a %s)" % (
        symbol, len(daily),
        _fmt(daily[0]["open_time"]), _fmt(daily[-1]["open_time"])))

    results = {}
    for name, cfg in [("Sistema 1 (20/10, con skip)", turtle.SYSTEM_1),
                       ("Sistema 2 (55/20, sin skip)", turtle.SYSTEM_2)]:
        trades, _open = turtle.backtest_system(daily, cfg["entry"], cfg["exit"], cfg["skip_filter"])
        wins = [t for t in trades if t["ganadora"]]
        total_r = sum(t["r_multiple"] for t in trades)
        wr = (100 * len(wins) / len(trades)) if trades else 0.0
        avg_r = (total_r / len(trades)) if trades else 0.0
        print("  %s: %d operaciones, %.1f%% acierto, expectativa total %+.2fR (%.3fR/operación de media)" % (
            name, len(trades), wr, total_r, avg_r))
        results[name] = (trades, total_r, wr)
    return results


def run_basket():
    agg = {"Sistema 1 (20/10, con skip)": [], "Sistema 2 (55/20, sin skip)": []}
    for symbol in BASKET:
        try:
            daily = binance.get_klines_deep(symbol, "1d", 5000)
        except Exception as e:
            print("ERROR con %s: %s" % (symbol, e))
            continue
        for name, cfg in [("Sistema 1 (20/10, con skip)", turtle.SYSTEM_1),
                           ("Sistema 2 (55/20, sin skip)", turtle.SYSTEM_2)]:
            trades, _open = turtle.backtest_system(daily, cfg["entry"], cfg["exit"], cfg["skip_filter"])
            agg[name].extend(trades)
            wins = sum(1 for t in trades if t["ganadora"])
            total_r = sum(t["r_multiple"] for t in trades)
            print("  %-6s %-28s setups=%3d  win_rate=%5.1f%%  expectativa=%+7.2fR" % (
                symbol, name, len(trades), (100 * wins / len(trades)) if trades else 0, total_r))

    print("\n" + "=" * 70)
    print("RESUMEN AGREGADO — %d activos" % len(BASKET))
    print("=" * 70)
    for name, trades in agg.items():
        wins = sum(1 for t in trades if t["ganadora"])
        total_r = sum(t["r_multiple"] for t in trades)
        wr = (100 * wins / len(trades)) if trades else 0
        avg_r = (total_r / len(trades)) if trades else 0
        print("%s: %d operaciones totales, %.1f%% acierto, expectativa %+.2fR (%.3fR/operación)" % (
            name, len(trades), wr, total_r, avg_r))


def _fmt(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--all" in args:
        run_basket()
    else:
        symbol = args[0].upper() if args else "ETH"
        run(symbol)
