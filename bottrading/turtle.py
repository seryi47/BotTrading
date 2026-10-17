"""Sistema Turtle Traders (Dennis/Eckhardt, 1983) — reglas públicamente
documentadas (Curtis Faith, "Way of the Turtle"; turtletrader.com/rules/),
adaptadas a un único activo/timeframe diario (el original operaba varios
futuros a la vez con límites de exposición correlacionada entre mercados,
que aquí no aplican por tratarse de un solo activo).

Simplificación deliberada y documentada: se implementa la señal de entrada
(ruptura de canal Donchian) + stop inicial (2N) + salida por reversión del
canal contrario — SIN pirámide de unidades adicionales (el original añade
hasta 4 unidades cada 0.5N a favor). Se simplifica así para aislar primero
si la señal base tiene ventaja real antes de añadir la complejidad de
gestionar varias unidades — ver bottrading/backtest_turtle.py."""

from . import indicators as ind_mod

# Parámetros de los dos sistemas originales (números públicos del propio
# sistema, no decisiones nuestras — a diferencia de granmago.py, aquí las
# cifras SÍ son las reglas literales documentadas).
SYSTEM_1 = {"entry": 20, "exit": 10, "skip_filter": True}
SYSTEM_2 = {"entry": 55, "exit": 20, "skip_filter": False}
N_PERIOD = 20          # EMA del True Range (ATR-like), igual que el original
STOP_N_MULT = 2.0      # stop inicial a 2N de la entrada (regla original)


def true_range_series(candles):
    out = []
    for i, c in enumerate(candles):
        if i == 0:
            out.append(c["high"] - c["low"])
        else:
            prev_close = candles[i - 1]["close"]
            out.append(max(c["high"] - c["low"], abs(c["high"] - prev_close), abs(c["low"] - prev_close)))
    return out


def n_series(candles, period=N_PERIOD):
    """N = EMA de `period` del True Range, en serie completa (una N por vela,
    alineada por índice) — se necesita la serie completa, no solo el último
    valor, porque el backtest recorre vela a vela."""
    tr = true_range_series(candles)
    return ind_mod.ema_series(tr, period)


def donchian(candles, idx, window, kind):
    """Máximo/mínimo de las `window` velas ANTERIORES a idx (sin incluir
    idx) — es la condición de ruptura: la vela idx "rompe" si su precio
    supera ese canal previo."""
    start = idx - window
    if start < 0:
        return None
    segment = candles[start:idx]
    if kind == "high":
        return max(c["high"] for c in segment)
    return min(c["low"] for c in segment)


def backtest_system(candles, entry_window, exit_window, skip_filter, min_lookback=100):
    """Recorre las velas (diarias) en orden, sin mirar al futuro: en cada
    vela, si hay posición abierta comprueba primero el stop y la salida por
    canal contrario (los dos EN LA MISMA vela: si ambos se darían, se asume
    el más conservador = el stop, porque no se puede saber cuál habría
    tocado antes dentro de la misma vela). Si no hay posición, comprueba
    ruptura de entrada. Devuelve (trades, posición_abierta_al_final) — la
    segunda es None si no queda ninguna posición abierta al llegar al final
    del histórico, o el dict de la posición viva si el sistema seguiría
    dentro ahora mismo (lo usa el bot en vivo para saber si hay que avisar)."""
    n = n_series(candles)
    trades = []
    position = None  # {"direction", "entry_price", "entry_idx", "stop", "n_at_entry"}
    last_signal_won = {"long": None, "short": None}  # para el filtro skip del Sistema 1

    for i in range(min_lookback, len(candles) - 1):  # -1: no operar sobre la vela en curso
        c = candles[i]
        n_i = n[i]
        if n_i is None or n_i <= 0:
            continue

        if position:
            direction = position["direction"]
            stop = position["stop"]
            exit_level = donchian(candles, i, exit_window, "low" if direction == "long" else "high")
            hit_stop = (c["low"] <= stop) if direction == "long" else (c["high"] >= stop)
            hit_exit = False
            if exit_level is not None:
                hit_exit = (c["low"] <= exit_level) if direction == "long" else (c["high"] >= exit_level)
            if hit_stop or hit_exit:
                # al tocar ambos en la misma vela, nos quedamos con el más conservador (el stop)
                exit_price = stop if hit_stop else exit_level
                risk = abs(position["entry_price"] - position["stop"])
                pnl = (exit_price - position["entry_price"]) if direction == "long" else (position["entry_price"] - exit_price)
                r_multiple = pnl / risk if risk > 0 else 0.0
                trades.append({
                    "direction": direction, "entry_idx": position["entry_idx"],
                    "entry_price": position["entry_price"], "exit_idx": i,
                    "exit_price": exit_price, "r_multiple": r_multiple,
                    "ganadora": r_multiple > 0,
                })
                last_signal_won[direction] = r_multiple > 0
                position = None
                continue  # no reabrir en la misma vela en la que se cerró

        if not position:
            hh = donchian(candles, i, entry_window, "high")
            ll = donchian(candles, i, entry_window, "low")
            if hh is not None and c["high"] > hh:
                if skip_filter and last_signal_won["long"] is True:
                    last_signal_won["long"] = None  # se "gasta" el skip, la siguiente sí cuenta
                else:
                    stop = c["close"] - STOP_N_MULT * n_i
                    position = {"direction": "long", "entry_price": c["close"],
                               "entry_idx": i, "stop": stop, "n_at_entry": n_i}
            elif ll is not None and c["low"] < ll:
                if skip_filter and last_signal_won["short"] is True:
                    last_signal_won["short"] = None
                else:
                    stop = c["close"] + STOP_N_MULT * n_i
                    position = {"direction": "short", "entry_price": c["close"],
                               "entry_idx": i, "stop": stop, "n_at_entry": n_i}

    return trades, position


def current_signal(candles, entry_window, exit_window, skip_filter, min_lookback=100):
    """Para el bot EN VIVO: corre la misma simulación sobre el histórico
    completo hasta ahora y devuelve el estado actual (posición abierta, si
    la hay, y el historial de operaciones cerradas). A propósito NO decide
    aquí si una entrada/cierre es "nueva" — eso depende de qué se avisó la
    última vez (estado del bot, no del mercado), y vivía mal aquí: la
    versión anterior solo marcaba "nueva" una entrada si coincidía con la
    ÚLTIMA vela cerrada justo en el momento de mirar, pero el chequeo diario
    no corre sincronizado con el cierre de la vela de Binance — si el
    chequeo llegaba unas horas tarde, la señal real "caducaba" sin haberse
    avisado nunca (bug real, encontrado el 17-oct-2026: ETH y BTC tenían
    señal real el 16-oct y nunca llegó el aviso). La decisión de "es nueva"
    ahora vive en Engine._maybe_check_turtle, comparando contra su propio
    dedup persistente, no contra la hora exacta del sondeo."""
    trades, open_pos = backtest_system(candles, entry_window, exit_window, skip_filter, min_lookback)
    return {"open_position": open_pos, "trades": trades}
