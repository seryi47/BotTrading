"""Modelos de datos comunes."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Level:
    """Un nivel a vigilar dentro de un activo. Es UNO de los dos:
    - price: un precio fijo en USD (soporte/resistencia de acción del precio).
    - ma: una media móvil en vivo ("sma20"|"sma50"|"sma200") que se recalcula
      en cada sondeo — usarla siempre que el nivel sea conceptualmente "cuando
      recupere/pierda tal media", para que no se quede con un número
      congelado a medida que la media se mueve con el tiempo."""

    id: int
    direction: str                 # "cae" (avisa al cruzar hacia abajo) | "sube" (al cruzar hacia arriba)
    price: Optional[float] = None
    ma: Optional[str] = None
    note: str = ""                 # comentario de lectura técnica
    created_by: str = "config"     # "config" (watches.yaml) | chat_id que lo creó por /vigilar

    def to_dict(self):
        d = {"id": self.id, "direction": self.direction, "note": self.note,
            "created_by": self.created_by}
        d["ma"] = self.ma if self.ma else None
        d["price"] = self.price if not self.ma else None
        return {k: v for k, v in d.items() if v is not None or k in ("note",)}

    @staticmethod
    def from_dict(d):
        return Level(id=d["id"], direction=d["direction"], ma=d.get("ma"),
                     price=float(d["price"]) if d.get("price") is not None else None,
                     note=d.get("note", ""), created_by=d.get("created_by", "config"))


@dataclass
class Indicators:
    """Snapshot técnico de un activo (mismo cálculo que usamos a mano en el chat)."""

    price: float
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma100: Optional[float] = None
    sma200: Optional[float] = None
    rsi14: Optional[float] = None
    macd_hist: Optional[float] = None
    high_30d: Optional[float] = None
    low_30d: Optional[float] = None

    def trend_desc(self) -> str:
        if self.sma20 is None or self.sma50 is None or self.sma200 is None:
            return "sin datos suficientes"
        if self.price > self.sma20 > self.sma50 > self.sma200:
            return "alcista limpia (precio > SMA20 > SMA50 > SMA200)"
        if self.price < self.sma20 < self.sma50 < self.sma200:
            return "bajista limpia (precio < SMA20 < SMA50 < SMA200)"
        if self.price > self.sma200:
            return "por encima de la media de 200 — fondo alcista con ruido de corto plazo"
        return "por debajo de la media de 200 — fondo bajista con ruido de corto plazo"

    def rsi_desc(self) -> str:
        if self.rsi14 is None:
            return "sin dato de RSI"
        if self.rsi14 >= 75:
            return "sobrecompra extrema (%.0f) — no perseguir" % self.rsi14
        if self.rsi14 >= 65:
            return "sobrecompra (%.0f)" % self.rsi14
        if self.rsi14 <= 30:
            return "sobreventa (%.0f) — posible zona de rebote" % self.rsi14
        if self.rsi14 <= 40:
            return "enfriado (%.0f)" % self.rsi14
        return "neutral (%.0f)" % self.rsi14
