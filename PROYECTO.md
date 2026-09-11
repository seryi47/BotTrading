# BotTrading

**Qué es:** bot de Telegram que vigila precios de cripto/acciones/fondos y
avisa de dos formas — al cruzar niveles de soporte/resistencia definidos a
mano, y de forma proactiva cada ~30 min si el propio RSI/MACD/medias dicen
que es zona de compra o hay un giro alcista — con lectura técnica incluida en
el aviso. Hermano de [BotViajes](../BotViajes), misma arquitectura (motor +
proveedores + comandos), dominio distinto.

**Estado (11-sept-2026):** en producción real, corriendo 24/7 en GitHub
Actions (repo público, job largo autorelevado — ver README para el porqué).
30 activos vigilados: 3 cripto, 22 acciones con señal de compra/venta, 5
fondos de MyInvestor solo informativos. Recibiendo avisos reales por
Telegram y ajustando el formato de los mensajes sobre la marcha según
feedback directo del usuario viendo los avisos llegar.

**Historial de la watchlist:**
- 23-ago-2026: watchlist inicial — BTC, ETH, MA, ORCL, AOSL, más SONO, TSLA,
  NVDA, CCJ, UEC, FCX, LINK añadidos ese mismo día tras análisis técnico.
- 09-sept-2026: se añaden los 5 fondos de MyInvestor (IWDA-MI, EM-MI, IUSN,
  BOND-MI, SGLD) para que aparezcan en el resumen diario junto a todo lo
  demás, sin señal de compra/venta (`dca: true`).
- 10-sept-2026: se añaden 12 valores más tras análisis a fondo — AMD, AVGO,
  MSFT, GOOGL, META, AMZN, AAPL, PLTR, SMCI, COIN, JPM, XOM.
- 11-sept-2026: se añade CELH (Celsius Holdings) — situación especial de
  reestructuración con presión activista y compra reciente del CEO en
  mínimos de 52 semanas.

**Decisiones de diseño que no son obvias leyendo el código:**
- Aviso de cruce de nivel **una vez por cruce**, no en bucle como BotViajes
  (un precio no desaparece como un asiento de tren; machacar Telegram no
  aporta nada aquí).
- Niveles guardados en USD (divisa nativa de los mercados); el euro es una
  conversión al mostrar, no el dato real — ver aviso en README y en `/ayuda`.
- `watches.yaml` no lleva `telegram_chat_id` a propósito (a diferencia del
  `config.yaml` de BotViajes): siempre sale de `.env` / secret de Actions,
  para poder tener el repo público sin exponer nada personal.
- El despliegue en GitHub Actions NO usa `schedule` como disparador
  principal — el registro de un cron nuevo puede tardar horas en activarse
  la primera vez (lo confirmamos en vivo: 2h30 sin disparar ni una vez). Se
  usa el mismo patrón que BotViajes: un job largo autorelevado
  (`python run.py --loop`) arrancado con `workflow_dispatch` (instantáneo y
  fiable), con el `schedule` solo de respaldo por si el job se cae.
- **Tras cualquier cambio de código, hay que reiniciar el job a mano**
  (cancelar + `workflow_dispatch`) para que se aplique ya — el job en
  marcha tiene el código viejo cargado en memoria y no lo relee hasta que
  se relanza. Ver comandos exactos en el README.
- La señal proactiva de 30 min (`entry_signal`) reutiliza el mismo caché de
  indicadores de 4h que ya existía (`history_ttl`) — no fuerza llamadas
  nuevas a la API cada 30 min, así que no añade carga extra sobre las APIs
  gratuitas de CoinGecko/Yahoo.
- Los mensajes de la señal proactiva se han iterado varias veces en
  producción según feedback real: separar el "giro alcista con respaldo de
  fondo" (precio también por encima de SMA200) del "giro alcista pero en
  tendencia bajista" (solo especulativo) en dos textos distintos, dar un
  precio de entrada concreto en líneas separadas ("ya mismo" / "más
  conservador") en vez de una sola línea densa, y espaciar los bloques del
  mensaje con líneas en blanco — todo esto porque el primer formato se leía
  confuso o contradictorio de un vistazo.

**Siguiente paso lógico si se retoma:**
- Revisar si los niveles del 23-ago-2026 (los 12 activos más antiguos)
  siguen vivos o hay que recalcularlos — llevan ya casi 3 semanas.
- Seguir recogiendo feedback real de los avisos de `entry_signal` (zona de
  compra / giro alcista) a medida que vayan llegando por Telegram — es la
  parte más nueva y menos probada en producción.
