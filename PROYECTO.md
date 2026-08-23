# BotTrading

**Qué es:** bot de Telegram que vigila precios de cripto/acciones y avisa al
cruzar niveles de soporte/resistencia, con lectura técnica (RSI/medias)
incluida en el aviso. Hermano de [BotViajes](../BotViajes), misma arquitectura
(motor + proveedores + comandos), dominio distinto.

**Estado:** recién creado (23-ago-2026), código completo y probado con
`--once` en local. Pendiente: rellenar `.env` con token/chat_id reales del
usuario y decidir modo de despliegue 24/7 (GitHub Actions gratis vs Oracle
Cloud Always Free — ver README).

**Watchlist inicial** (`watches.yaml`): BTC, ETH, Mastercard (MA), Oracle
(ORCL) y Alpha and Omega Semiconductor (AOSL) — esta última como "muy barata
con potencial": cotiza cerca de mínimos de 52 semanas tras un mal encaje de
resultados el 12-ago-2026, sin beneficios (P/E negativo, así que no es
"barata" en el sentido de múltiplo bajo sino en precio absoluto vs. sus
máximos), con objetivo de analistas ~65% por encima del precio actual si el
negocio de semis de potencia para IA/servidores sigue creciendo. Riesgo alto,
posición pequeña si se entra.

**Decisiones de diseño que no son obvias leyendo el código:**
- Aviso **una vez por cruce**, no en bucle como BotViajes (un precio no
  desaparece como un asiento de tren; machacar Telegram no aporta nada aquí).
- Niveles guardados en USD (divisa nativa de los mercados); el euro es una
  conversión al mostrar, no el dato real — ver aviso en README y en `/ayuda`.
- `watches.yaml` no lleva `telegram_chat_id` a propósito (a diferencia del
  `config.yaml` de BotViajes): siempre sale de `.env` / secret de Actions,
  para poder tener el repo público sin exponer nada personal.

**Siguiente paso lógico si se retoma:** decidir despliegue 24/7 y, con el
tiempo, revisar si los niveles de `watches.yaml` siguen vivos o hay que
recalcularlos (el mercado no espera).
