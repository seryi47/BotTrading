"""Metodología técnica de GranMago (ver memoria persistente
metodologia-trading-granmago.md) convertida en código: filtro de tendencia
multi-timeframe, estructura de máximos/mínimos, imbalances (FVG), detección
de manipulación/barrido de liquidez y la checklist de confirmación de
entrada de la clase 13, con sugerencia de stop loss (clase 11) y take
profit (clase 12).

IMPORTANTE — honestidad sobre lo que es del curso y lo que es decisión
nuestra: el curso NUNCA da umbrales numéricos para "cuántas velas definen un
swing", "qué tamaño de mecha es grande" ni "cuántos toques hacen una
confluencia válida". Los parámetros de abajo (SWING_WINDOW, SWEEP_LOOKBACK,
CONFLUENCE_BAND_PCT, STOP_MARGIN_PCT) son decisiones propias razonables, NO
reglas literales de GranMago — están aislados en constantes para poder
ajustarlos con la experiencia real del bot, tal como se hizo con el resto
de BotTrading."""

from . import indicators as ind_mod
from .providers import kraken  # Binance bloquea (451) desde GitHub Actions — ver bottrading/providers/kraken.py.
# GranMago está desactivado (granmago_symbols: [] en watches.yaml, 16-oct-2026) pero si se
# reactiva algún día, que arranque ya con la fuente de datos que SÍ funciona en vivo (19-oct-2026).

SWING_WINDOW = 3          # velas a cada lado para que un punto cuente como swing high/low (decisión propia)
SWEEP_LOOKBACK = 12       # nº de velas (en la temporalidad operativa) donde buscar una manipulación reciente
CONFLUENCE_BAND_PCT = 0.015   # dos swings cuentan como "misma zona" si están a <=1.5% uno de otro (decisión propia)
STOP_MARGIN_PCT = 0.01    # margen extra que se añade al swing barrido al sugerir el stop loss (decisión propia)
SWING_RECENCY_CANDLES = 90   # un swing del timeframe superior solo cuenta como "liquidez relevante" si
# está dentro de las últimas 90 velas de ESE timeframe (en diario, ~3 meses) — sin esto, el backtest del
# 16-oct-2026 encontró barridos de máximos/mínimos de hace más de un año, dando stops de hasta el 30% del
# precio (nada que ver con lo que un trader real vigilaría). Decisión propia, no una cifra del curso.
MIN_RR = 0.0   # SIN filtro — ver nota larga en granmago.py. El backtest del 16-oct-2026 probó 0.5, 1.0 y
# 1.5 buscando un TP más lejano para "mejorar" el ratio, y la expectativa real EMPEORÓ en los tres casos
# (de +0.47R sin filtro a -1.13R, -4.78R y -6.03R con cada umbral) frente a la confluencia más cercana sin
# exigir nada — con solo 4-19 operaciones de muestra, cualquier filtro adicional es ruido, no señal. Se deja
# la constante y el campo "riesgo_beneficio" en el resultado para que el bot pueda MOSTRAR el R:R real de
# cada setup (el usuario decide si le compensa), en vez de que el código decida por él con un umbral inventado.


def _closes(candles):
    return [c["close"] for c in candles]


def _highs(candles):
    return [c["high"] for c in candles]


def _lows(candles):
    return [c["low"] for c in candles]


def ema50_bias(candles):
    """'alcista' si el último cierre está por encima de la EMA50 de esa
    temporalidad, 'bajista' si está por debajo, None si no hay histórico
    suficiente. Se usa en semanal/diario/4h (clases 2 y 6)."""
    closes = _closes(candles)
    e = ind_mod.ema(closes, 50)
    if e is None:
        return None, None
    return ("alcista" if closes[-1] > e else "bajista"), e


def swing_points(candles, window=SWING_WINDOW):
    """Fractal simple: un punto es swing high/low si su máximo/mínimo es el
    mayor/menor dentro de `window` velas a cada lado. No usa la última vela
    (en curso, sin cerrar) ni las primeras/últimas `window` velas del array.
    Devuelve lista de dicts {idx, type: 'high'|'low', price}, en orden cronológico."""
    highs, lows = _highs(candles), _lows(candles)
    n = len(candles)
    out = []
    for i in range(window, n - window - 1):  # -1 para excluir la vela en curso
        window_highs = highs[i - window:i + window + 1]
        window_lows = lows[i - window:i + window + 1]
        if highs[i] == max(window_highs):
            out.append({"idx": i, "type": "high", "price": highs[i]})
        if lows[i] == min(window_lows):
            out.append({"idx": i, "type": "low", "price": lows[i]})
    return out


def confluence_zone(prices, band_pct=CONFLUENCE_BAND_PCT):
    """De una lista de precios YA FILTRADA por el llamador (p.ej. solo swing
    highs que están por delante del precio actual en la dirección de la
    operación), agrupa los que caen dentro de una banda de `band_pct` entre
    sí; devuelve TODOS los grupos como lista de (precio_representativo,
    nº_de_toques) — es el criterio de "confluencia" de las clases 6/8/12/13
    (GranMago nunca cuantifica cuántos toques hacen una zona válida, aquí se
    cuenta de verdad). El llamador decide qué grupo usar (p.ej. el más
    cercano al precio actual para un take profit, el "próximo objetivo")."""
    if not prices:
        return []
    pts = sorted(prices)
    groups, used = [], set()
    for i, p in enumerate(pts):
        if i in used:
            continue
        group_idx = [j for j, q in enumerate(pts) if abs(q - p) / p <= band_pct]
        used.update(group_idx)
        group_vals = [pts[j] for j in group_idx]
        groups.append((sum(group_vals) / len(group_vals), len(group_vals)))
    return groups


def detect_imbalances(candles, lookback=40):
    """Imbalance/FVG de 3 velas (clase 5): hueco entre la mecha de la vela 1
    y la de la vela 3 de un movimiento impulsivo. Devuelve los que siguen
    SIN RELLENAR (ninguna vela posterior ha entrado en el hueco), como lista
    de dicts {type: 'alcista'|'bajista', low, high}."""
    start = max(1, len(candles) - lookback)
    out = []
    for i in range(start, len(candles) - 2):
        c1, c3 = candles[i], candles[i + 2]
        if c1["high"] < c3["low"]:  # hueco alcista (impulso al alza)
            gap_low, gap_high = c1["high"], c3["low"]
            filled = any(c["low"] <= gap_low for c in candles[i + 3:])
            if not filled:
                out.append({"type": "alcista", "low": gap_low, "high": gap_high})
        elif c1["low"] > c3["high"]:  # hueco bajista (impulso a la baja)
            gap_low, gap_high = c3["high"], c1["low"]
            filled = any(c["high"] >= gap_high for c in candles[i + 3:])
            if not filled:
                out.append({"type": "bajista", "low": gap_low, "high": gap_high})
    return out


def detect_sweep(candles, swings, lookback=SWEEP_LOOKBACK):
    """Manipulación/barrido de liquidez (clase 8): una vela, dentro de las
    últimas `lookback`, rompe con la MECHA un swing low/high previo y
    CIERRA de vuelta dentro (no se queda fuera). Devuelve el barrido más
    reciente como dict {type:'low'|'high', swing_price, pierce_price,
    idx} o None si no hay ninguno."""
    n = len(candles)
    recent_start = max(0, n - 1 - lookback)
    best = None
    for s in swings:
        if s["idx"] >= recent_start:
            continue  # el swing tiene que ser PREVIO a la ventana de barrido
        for i in range(max(s["idx"] + 1, recent_start), n - 1):  # -1: excluye vela en curso
            c = candles[i]
            if s["type"] == "low" and c["low"] < s["price"] and c["close"] > s["price"]:
                if best is None or i > best["idx"]:
                    best = {"type": "low", "swing_price": s["price"], "pierce_price": c["low"], "idx": i}
            elif s["type"] == "high" and c["high"] > s["price"] and c["close"] < s["price"]:
                if best is None or i > best["idx"]:
                    best = {"type": "high", "swing_price": s["price"], "pierce_price": c["high"], "idx": i}
    return best


def confirmation_close(candles, sweep, closes_needed=1):
    """Clase 13: tras el barrido, ¿ha cerrado el precio `closes_needed` vela(s)
    recuperando el nivel (por encima del swing low barrido, o por debajo del
    swing high barrido)? Cuenta velas CERRADAS después del barrido, sin
    contar la vela en curso."""
    if sweep is None:
        return False, 0
    closed = candles[sweep["idx"] + 1:-1]  # excluye vela en curso
    if sweep["type"] == "low":
        ok = [c for c in closed if c["close"] > sweep["swing_price"]]
    else:
        ok = [c for c in closed if c["close"] < sweep["swing_price"]]
    # exige que sean las ÚLTIMAS velas (recuperación sostenida, no un cierre
    # suelto seguido de volver a perder el nivel)
    consecutive = 0
    for c in reversed(closed):
        cond = c["close"] > sweep["swing_price"] if sweep["type"] == "low" else c["close"] < sweep["swing_price"]
        if cond:
            consecutive += 1
        else:
            break
    return consecutive >= closes_needed, consecutive


def build_setup(symbol, name, closes_needed=1):
    """Checklist completa de la clase 13 aplicada a un símbolo (p.ej. 'ETH'),
    con datos EN VIVO de Binance. Ver compute_setup() para la lógica pura
    (sin red), que es la que se reutiliza en el backtest."""
    # Histórico amplio (no solo lo mínimo para calcular EMA50): una EMA de
    # ventana 50 arrancada con pocas decenas de velas no converge bien aunque
    # la semilla sea correcta (bug verificado el 16-oct-2026: con 60 velas
    # semanales daba 2.642 en vez de ~2.422 reales) — 300 velas da margen de
    # sobra en las tres temporalidades.
    weekly = kraken.get_klines(symbol, "1w", 300)
    daily = kraken.get_klines(symbol, "1d", 300)
    h4 = kraken.get_klines(symbol, "4h", 300)
    return compute_setup(weekly, daily, h4, symbol, name, closes_needed)


def compute_setup(weekly, daily, h4, symbol, name, closes_needed=1):
    """Lógica PURA de la checklist (sin llamadas de red): 1) tendencia
    semanal+diaria (EMA50), 2) swings del timeframe superior (diario), 3)
    barrido reciente de uno de esos swings, 4) confirmación por cierre de
    vela en el timeframe inferior (4h) recuperando una zona de confluencia,
    5) sugerencia de SL (clase 11) y TP (clase 12). Recibe las velas ya
    cargadas (de Binance en vivo, o recortadas a una fecha pasada para
    backtesting — ver bottrading/backtest_granmago.py) para poder reutilizar
    exactamente el mismo código en ambos casos sin duplicar lógica.

    Devuelve un dict con todo el análisis (incluso si NO hay setup completo,
    para poder explicar qué falta) con la clave 'setup_valido': bool."""
    bias_w, ema_w = ema50_bias(weekly)
    bias_d, ema_d = ema50_bias(daily)
    # h4[:-1]: la convención en todo este módulo es que el último elemento de
    # `h4` es la vela EN CURSO (ver `price` más abajo, que usa h4[-2]) — bias_4h
    # tiene que mirar la misma última vela CERRADA, no la que aún se está
    # formando (inconsistencia real encontrada en la auditoría del 16-oct-2026;
    # no afectaba al resultado del backtest porque bias_4h es solo informativo,
    # no decide la dirección, pero sí hacía el dato mostrado incorrecto).
    bias_4h, ema_4h = ema50_bias(h4[:-1])

    swings_daily = swing_points(daily)
    swings_4h = swing_points(h4)

    price = h4[-2]["close"]  # última vela 4h CERRADA, no la que está en curso

    # Dirección a buscar: a favor de la tendencia semanal (clase 1: la
    # tendencia mayor manda). Si semanal es alcista, buscamos barrido de
    # MÍNIMOS (para long); si es bajista, barrido de MÁXIMOS (para short).
    direction = "long" if bias_w == "alcista" else "short" if bias_w == "bajista" else None

    # Solo cuentan como "liquidez relevante" los swings diarios RECIENTES
    # (ver SWING_RECENCY_CANDLES) — sin este filtro, un movimiento de precio
    # normal con el tiempo acaba "barriendo" mínimos/máximos de hace más de
    # un año, dando stops a decenas de % de distancia (verificado en backtest).
    recent_daily = swings_daily[-SWING_RECENCY_CANDLES:] if len(swings_daily) > SWING_RECENCY_CANDLES else swings_daily

    sweep = None
    if direction == "long":
        lows_daily = [s for s in recent_daily if s["type"] == "low"]
        sweep = detect_sweep(h4, lows_daily)
    elif direction == "short":
        highs_daily = [s for s in recent_daily if s["type"] == "high"]
        sweep = detect_sweep(h4, highs_daily)

    confirmed, n_closes = confirmation_close(h4, sweep, closes_needed) if sweep else (False, 0)

    imbalances_4h = detect_imbalances(h4)

    setup_valido = bool(direction and sweep and confirmed)

    result = {
        "symbol": symbol, "name": name, "direction": direction, "price": price,
        "bias_semanal": bias_w, "bias_diario": bias_d, "bias_4h": bias_4h,
        "ema50_4h": ema_4h,
        "sweep": sweep, "confirmado": confirmed, "n_cierres_confirmacion": n_closes,
        "imbalances_4h": imbalances_4h,
        "setup_valido": setup_valido,
    }
    if not setup_valido:
        return result

    # --- Stop loss (clase 11): margen por debajo/encima del nivel barrido,
    # ampliado si hay un imbalance sin rellenar aún más allá (más protección). ---
    if direction == "long":
        stop = sweep["pierce_price"] * (1 - STOP_MARGIN_PCT)
        lower_imb = [i for i in imbalances_4h if i["type"] == "alcista" and i["high"] < price]
        if lower_imb:
            deepest = min(lower_imb, key=lambda i: i["low"])
            stop = min(stop, deepest["low"] * (1 - STOP_MARGIN_PCT))
    else:
        stop = sweep["pierce_price"] * (1 + STOP_MARGIN_PCT)
        upper_imb = [i for i in imbalances_4h if i["type"] == "bajista" and i["low"] > price]
        if upper_imb:
            highest = max(upper_imb, key=lambda i: i["high"])
            stop = max(stop, highest["high"] * (1 + STOP_MARGIN_PCT))

    # --- Take profit (clase 12): próxima zona de confluencia de swings
    # diarios en la dirección del movimiento. Se prefiere una zona con >=2
    # toques (confluencia real) sobre la más cercana a secas.
    #
    # Backtest del 16-oct-2026 en ETH (~14 meses, 4h, 3 variantes probadas):
    #   - TP = confluencia más CERCANA (esta):            expectativa +0.47R (19 trades, ganancia media pequeña,
    #                                                       muchos aciertos de poco beneficio cada uno)
    #   - TP = primera confluencia con R:R>=1.0:            expectativa -4.78R (16 trades) — PEOR
    #   - TP = primera confluencia con R:R>=1.5:            expectativa -6.03R (14 trades) — AÚN PEOR
    # Forzar un TP más lejano para "mejorar" el ratio empeoró el resultado
    # real: el precio rara vez llega tan lejos antes de tocar el stop. Nos
    # quedamos con la confluencia más cercana (lo que de verdad funcionó
    # mejor en el backtest), con MIN_RR solo como suelo para descartar los
    # casos degenerados (R:R casi cero), no como objetivo a perseguir. ---
    tp_kind = "high" if direction == "long" else "low"
    candidates = [s["price"] for s in swings_daily if s["type"] == tp_kind and
                  ((s["price"] > price) if direction == "long" else (s["price"] < price))]
    risk = abs(price - stop)

    groups = confluence_zone(candidates) if candidates else []
    strong_groups = [g for g in groups if g[1] >= 2]
    tp_price, tp_touches = (None, 0)
    if strong_groups:
        tp_price, tp_touches = min(strong_groups, key=lambda g: abs(g[0] - price))
    elif groups:
        tp_price, tp_touches = min(groups, key=lambda g: abs(g[0] - price))
    rr = (abs(tp_price - price) / risk) if (tp_price is not None and risk > 0) else None
    rr_ok = rr is not None and rr >= MIN_RR

    result.update({
        "stop_loss": stop, "take_profit": tp_price, "take_profit_touches": tp_touches,
        "riesgo_beneficio": rr, "confluencia_baja": tp_touches < 2,
    })
    if not rr_ok:
        result["setup_valido"] = False
        result["motivo_descarte"] = (
            "estructura y confirmación correctas, pero el ratio riesgo/beneficio (%.2f) "
            "queda por debajo del mínimo exigido (%.1f) — %s"
            % (rr if rr is not None else 0.0, MIN_RR,
               "no hay zona de TP por delante" if tp_price is None else
               "el TP más cercano con confluencia está demasiado pegado al precio")
        )
    return result
