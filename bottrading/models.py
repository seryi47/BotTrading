"""Modelos de datos comunes."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Level:
    """Un nivel de precio a vigilar dentro de un activo."""

    id: int
    price: float                 # nivel en USD (divisa nativa del mercado)
    direction: str                # "cae" (avisa al cruzar hacia abajo) | "sube" (al cruzar hacia arriba)
    note: str = ""                # comentario de lectura técnica
    created_by: str = "config"    # "config" (watches.yaml) | chat_id que lo creó por /vigilar

    def to_dict(self):
        return {"id": self.id, "price": self.price, "direction": self.direction,
                "note": self.note, "created_by": self.created_by}

    @staticmethod
    def from_dict(d):
        return Level(id=d["id"], price=float(d["price"]), direction=d["direction"],
                     note=d.get("note", ""), created_by=d.get("created_by", "config"))


@dataclass
class Indicators:
    """Snapshot técnico de un activo (mismo cálculo que usamos a mano en el chat)."""

    price: float
    sma20: Optional[float] = None
    sma50: Optional[float] = None
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
