"""Indicadores técnicos — la misma aritmética que hemos usado a mano en el chat
(SMA/EMA/RSI de Wilder/MACD 12-26-9), aquí convertida en código reutilizable."""

from .models import Indicators


def sma(values, window):
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema_series(values, window):
    if not values:
        return []
    k = 2 / (window + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def ema(values, window):
    if len(values) < window:
        return None
    return ema_series(values, window)[-1]


def rsi(values, period=14):
    if len(values) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values, fast=12, slow=26, signal=9):
    if len(values) < slow + signal:
        return None, None, None
    ema_fast = ema_series(values, fast)
    ema_slow = ema_series(values, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema_series(macd_line, signal)
    return macd_line[-1], signal_line[-1], macd_line[-1] - signal_line[-1]


def read(closes):
    """Calcula el snapshot técnico completo a partir de una serie de cierres
    diarios (cronológica, el último es el más reciente)."""
    if not closes:
        return None
    price = closes[-1]
    _m, _s, hist = macd(closes)
    window30 = closes[-30:] if len(closes) >= 30 else closes
    return Indicators(
        price=price,
        sma20=sma(closes, 20),
        sma50=sma(closes, 50),
        sma100=sma(closes, 100),
        sma200=sma(closes, 200),
        rsi14=rsi(closes, 14),
        macd_hist=hist,
        high_30d=max(window30),
        low_30d=min(window30),
    )


def resolve_level_price(level, ind):
    """Precio "vivo" de un nivel: si el nivel referencia una media (level["ma"]
    = "sma20"|"sma50"|"sma100"|"sma200"), se recalcula con el indicador de hoy en vez de
    quedarse congelado en el precio que tenía esa media el día que se definió
    el nivel. Si el nivel lleva un precio fijo ("price"), ese no cambia nunca
    (para soportes/resistencias de acción del precio, que no son una media)."""
    if level.get("ma"):
        return getattr(ind, level["ma"], None) if ind else None
    return level.get("price")


def nearest_levels(price, levels):
    """De los niveles configurados de un activo, el soporte (cae) y la
    resistencia (sube) más cercanos al precio actual — para el resumen diario."""
    supports = [lv for lv in levels if lv["direction"] == "cae"]
    resistances = [lv for lv in levels if lv["direction"] == "sube"]

    def closest(cands, want_below):
        if not cands:
            return None
        side = [lv for lv in cands if (lv["price"] <= price) == want_below]
        pool = side or cands
        return min(pool, key=lambda lv: abs(lv["price"] - price))

    return closest(supports, True), closest(resistances, False)


def overall_signal(ind: "Indicators"):
    """Semáforo de "¿compro o no?" para el resumen diario, a partir del RSI.
    Misma regla de siempre: sobrecompra no se persigue, sobreventa se vigila."""
    if ind is None or ind.rsi14 is None:
        return "⚪", "Sin datos suficientes ahora mismo — reintento en el próximo sondeo."
    r = ind.rsi14
    if r >= 75:
        return "🔴", "No comprar — sobrecompra extrema, alto riesgo de vela de vuelta."
    if r >= 65:
        return "🟠", "Cuidado, sobrecompra — mejor esperar una corrección antes de entrar."
    if r <= 30:
        return "🟢", "Sobreventa — posible zona de rebote, vigilar confirmación."
    if r <= 45:
        return "🟢", "RSI enfriado — zona razonable si el resto del cuadro acompaña."
    return "🟡", "Neutral — sin señal clara, ni para entrar ni para salir."


def buy_plan(rsi14, support, resistance, fmt):
    """Condición concreta de entrada para el resumen diario — "cuándo comprar",
    no solo "cómo está ahora". `fmt` formatea un precio (para no acoplar esto
    a fx aquí)."""
    if rsi14 is None:
        return "Sin RSI todavía — reintento en el próximo sondeo."
    if rsi14 >= 65:
        if support:
            return "que caiga a %s Y el RSI baje de 45 — no antes, aunque tenga buena pinta." % fmt(support["price"])
        return "que el RSI baje de 45 (ahora está en sobrecompra)."
    if rsi14 <= 45:
        if support:
            return "ya está en zona razonable (RSI %.0f) — confírmalo con un rebote sin perder %s." % (rsi14, fmt(support["price"]))
        return "ya está en zona razonable (RSI %.0f)." % rsi14
    if support and resistance:
        return "rebota en %s manteniendo el RSI por debajo de 65, o rompe %s con volumen." % (fmt(support["price"]), fmt(resistance["price"]))
    return "aparezca una señal más clara — el RSI está neutral ahora mismo."


def classify_alert(direction, ind: "Indicators"):
    """Etiqueta de trader para un cruce de nivel: compra / evitar / vigilar.

    Es la regla que hemos aplicado todo el rato en el chat: no perseguir en
    sobrecompra, y un soporte solo vale si el RSI ya se ha enfriado."""
    rsi14 = ind.rsi14 if ind else None
    if direction == "cae":
        if rsi14 is not None and rsi14 <= 45:
            return "🟢 Posible zona de compra (RSI ya enfriado)"
        if rsi14 is not None and rsi14 >= 65:
            return "🟡 Toca soporte pero el RSI (%.0f) sigue alto — esperar confirmación, no comprar solo por el nivel" % rsi14
        return "🟡 Soporte tocado — vigilar si rebota antes de entrar"
    else:  # "sube"
        if rsi14 is not None and rsi14 >= 75:
            return "🔴 Rompe resistencia pero con RSI en sobrecompra extrema (%.0f) — no perseguir" % rsi14
        if rsi14 is not None and rsi14 <= 55:
            return "🟢 Rompe resistencia con margen de RSI (%.0f) — continuación con más credibilidad" % rsi14
        return "🟡 Resistencia rota — vigilar que aguante antes de sumar"
