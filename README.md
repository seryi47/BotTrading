# BotTrading 📈🔔

Vigila el precio de 30 activos (cripto, acciones, y 5 fondos de MyInvestor) y
avisa por Telegram de dos formas distintas — al **cruzar un nivel** definido
a mano, y de forma **proactiva cada ~30 min** si el propio RSI/MACD/medias
dicen que ahora mismo es zona de compra o hay un giro alcista — siempre con
lectura técnica incluida en el aviso, no solo el número desnudo. Misma
arquitectura que [BotViajes](../BotViajes), adaptada de "avisar cuando hay
billete" a "avisar cuando el precio hace lo que llevamos vigilando".

- Precios en vivo: CoinGecko (cripto) y Yahoo Finance (acciones), sin API key.
- Cada aviso lleva el precio en USD **y en euros** (conversión con el tipo de
  cambio del día — el mercado real cotiza en USD, ver nota en `/ayuda`).
- Los niveles de `watches.yaml` son los que hemos ido calculando a mano en el
  chat: soportes/resistencias, SMA20/50/100/200, objetivos de analistas, y la
  regla de "no perseguir con RSI en sobrecompra" aplicada automáticamente.
- Resumen diario por Telegram (hora configurable) con el estado de todos los
  activos, aunque no haya saltado ningún nivel.
- Añade tus propios niveles a mano desde Telegram con `/vigilar`, en cualquier
  cripto o acción, no solo las de la watchlist inicial.
- Se para y se reanuda desde Telegram (`/pausa`, `/seguir`, `/apagar`).

## Los 30 activos vigilados ahora mismo

- **Cripto (3):** BTC, ETH, LINK
- **Acciones con señal de compra/venta (22):** MA, ORCL, AOSL, SONO, TSLA,
  NVDA, CCJ, UEC, FCX, AMD, AVGO, MSFT, GOOGL, META, AMZN, AAPL, PLTR, SMCI,
  COIN, JPM, XOM, CELH
- **Fondos de MyInvestor, solo informativos (5, `dca: true`):** IWDA-MI,
  EM-MI, IUSN, BOND-MI, SGLD — cronometrar una aportación mensual a un fondo
  indexado no tiene la misma lógica que una acción suelta, así que estos NO
  llevan niveles ni señales de "compra/no compra", solo precio + contexto en
  el resumen diario.

## Dos tipos de aviso — no los confundas

### 1. Cruce de nivel (evento, no repite)
Cada nivel de `watches.yaml` (o creado con `/vigilar`) avisa **una vez**, en
el instante exacto en que el precio lo cruza — no cada vez que sigue por
encima/debajo de un nivel ya cruzado antes (ver más abajo "Cómo decide cruce
de nivel"). Es lo mismo de siempre, sin cambios.

### 2. Señal proactiva por RSI/MACD (cada ~30 min, avisa en el CAMBIO)
Añadido en sept-2026. Independiente de que se cruce ningún nivel manual: cada
`signal_check_interval` segundos (1800 por defecto, configurable en
`watches.yaml`), el motor revisa el RSI/MACD/medias de cada activo (excepto
los fondos `dca`) y detecta dos situaciones (`indicators.entry_signal`):

- **🟢 Zona de compra** — RSI≤30 (sobreventa real).
- **🚀 Giro alcista** — MACD en positivo, RSI 50-65 (con margen antes de
  sobrecompra) y precio por encima de su SMA20. Se distingue explícitamente
  si además ya cotiza por encima de su SMA200 ("con respaldo de fondo", más
  fiable) o si sigue por debajo ("dentro de una tendencia bajista", solo
  especulativo con tamaño reducido) — el mensaje lo explica en texto plano,
  no solo con los números sueltos.

**Solo avisa en el cambio de estado**, igual que un cruce de nivel: si sigue
en la misma zona 30 min después, no repite el aviso; si sale y vuelve a
entrar, sí avisa de nuevo. El estado se guarda por activo
(`asset["signal_state"]`) y persiste en `state_file`.

Cada aviso de este tipo incluye, además del texto explicativo:
- 💰 **Precio de entrada** — el actual y, si hay soporte definido, el más
  conservador (retroceso a ese soporte).
- 📍 Soporte/resistencia más cercanos con su distancia en %.
- 🎯 **Confirmación** — la misma condición "compraría si..." que ya usa el
  resumen diario (`indicators.buy_plan`).

## Instalación

```sh
cd ~/Desktop/BotTrading
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env    # pega tu token y chat_id de Telegram
```

### Telegram (obligatorio)
1. Abre **@BotFather** en Telegram → `/newbot` → te da el **token**.
2. Abre tu bot y pulsa **Start**.
3. Abre **@userinfobot** → te dice tu **chat id**.
4. Pega ambos en `.env`.

Comprueba que llega:
```sh
./venv/bin/python run.py --test-telegram
```

## Uso

### Modo A — proceso continuo (`run.py`)
```sh
./venv/bin/python run.py            # vigilancia continua, sondeo cada POLL_INTERVAL
./venv/bin/python run.py --once     # una comprobación y sale
./venv/bin/python run.py --loop     # bucle largo autorelevado (ver despliegue en la nube)
```

### Modo B — bot interactivo (`bot.py`)
```sh
./venv/bin/python bot.py
```
Deja que gestiones niveles chateando con el bot (`/vigilar`, `/borrar`, `/lista`...).

### Comandos de Telegram
```
/lista                                 activos y niveles vigilados
/precio SYMBOL                         precio actual (ej. /precio BTC)
/analisis SYMBOL [cripto|accion]       lectura técnica completa al momento
/estado                                ¿vigilando o en pausa?
/vigilar SYMBOL; cripto|accion; PRECIO; cae|sube; [nota]
/borrar <id_nivel>                     quitar un nivel (el id sale en /lista)
/pausa | /seguir                       parar / reanudar sin apagarse
/apagar si                             apagarse del todo
```

Ejemplos:
```
/vigilar BTC; cripto; 69000; cae; soporte SMA200, zona de compra
/vigilar ORCL; accion; 150; sube; rompe SMA50
/analisis TSEM accion
```

### Dejarlo corriendo en tu Mac
```sh
cd ~/Desktop/BotTrading
nohup ./venv/bin/python bot.py >> bottrading.log 2>&1 &
tail -f bottrading.log
pkill -f bot.py
```

### En la nube 24/7 sin tarjeta (GitHub Actions) — cómo funciona de verdad
`.github/workflows/vigilar.yml` NO dispara un job corto cada 5 min por
`schedule` — el registro de un cron nuevo en GitHub puede tardar horas (o
directamente atascarse) en activarse la primera vez, y no es fiable para algo
que necesita correr sin interrupción. En su lugar:

- Se lanza **un único job largo** (`python -u run.py --loop`) que hace su
  propio bucle interno con `LOOP_INTERVAL` (sondeo de precio) durante hasta
  `MAX_RUNTIME_SECONDS` (~5h33m, por debajo del límite de 340 min del job).
- El `schedule: cron: "*/5 * * * *"` de arriba es solo un **respaldo/relevo**:
  si el job actual se cae o llega a su límite, el siguiente disparo del
  schedule (o un `workflow_dispatch` manual) arranca uno nuevo.
- `concurrency: group: vigilar-loop, cancel-in-progress: false` evita que
  haya dos jobs corriendo a la vez — uno nuevo se encola detrás del activo.
- **Si cambias código y quieres que se aplique ya**, no basta con hacer
  `git push`: el job en marcha ya tiene el código viejo cargado en memoria.
  Hay que cancelarlo y relanzarlo a mano:
  ```sh
  gh run list --repo <tu-usuario>/BotTrading --workflow=vigilar.yml --limit 1
  gh run cancel <run_id> --repo <tu-usuario>/BotTrading
  gh workflow run vigilar.yml --repo <tu-usuario>/BotTrading
  ```
  `workflow_dispatch` es instantáneo y fiable (a diferencia del `schedule`
  para la PRIMERA activación), así que es la forma segura de forzar un
  reinicio.
- Repo **público** (los secrets siguen siendo privados) para minutos de
  Actions gratis e ilimitados — con repo privado este patrón de job largo
  consumiría la cuota mensual gratuita muy rápido.
- Configura en *Settings → Secrets and variables → Actions*:
  `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. La watchlist que vigila es
  `watches.yaml` (versionado); edítala y haz `git push` para cambiarla — pero
  recuerda que, igual que con el código, no se aplica hasta el próximo
  relevo salvo que reinicies a mano.
- El resumen diario se commitea a `state/last_digest.json` (sin datos
  personales) para no repetirse si el job se relevó después de la hora del
  resumen.

### En un servidor propio (Oracle Cloud Always Free, systemd)
`deploy/bottrading.service` arranca `bot.py` solo al reiniciar. Copia el
proyecto al servidor, crea el venv, ajusta rutas/usuario en el `.service` y:
```sh
sudo cp deploy/bottrading.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bottrading
```

## Dos tipos de nivel: precio fijo o media en vivo
Un nivel en `watches.yaml` (o creado con `/vigilar`) es **uno de los dos**:
- `price: 26` — un precio fijo. Para soportes/resistencias de acción del
  precio, máximos/mínimos de 52 semanas, niveles psicológicos, objetivos de
  analistas.
- `ma: sma20|sma50|sma100|sma200` — una **media móvil en vivo**: se recalcula
  en cada sondeo con `indicators.resolve_level_price()`, no se queda
  congelada en el número que tenía el día que se definió. Úsalo siempre que
  el nivel sea conceptualmente "cuando recupere/pierda tal media" — si se
  pusiera como precio fijo, en unas semanas ese número ya no coincidiría con
  dónde está esa media de verdad. `/vigilar SYMBOL; accion; sma200; sube;
  nota` también acepta este tipo desde Telegram.

## Cómo decide "cruce de nivel"
Cada activo guarda el último precio conocido (`last_price`). En cada sondeo
compara el precio nuevo contra cada nivel:
- `cae`: avisa si el precio **estaba por encima** del nivel y ahora está
  **en o por debajo**.
- `sube`: avisa si el precio **estaba por debajo** y ahora está **en o por
  encima**.

Así solo avisa en el cruce real, no cada vez que el precio simplemente sigue
por debajo/encima de un nivel ya cruzado antes.

## Cómo decide "es buena zona o no"
Misma regla de siempre (no perseguir sobrecompra, soporte solo vale si el RSI
ya se enfrió), aplicada en dos sitios distintos del código:
- **Al cruzar un nivel manual** (`indicators.classify_alert`): 🟢 posible
  compra / 🟡 esperar confirmación / 🔴 no perseguir, según el RSI en ese
  instante.
- **En la señal proactiva cada 30 min** (`indicators.entry_signal`): ver
  arriba, "Señal proactiva por RSI/MACD".
- **En el resumen diario** (`indicators.overall_signal` + `buy_plan`): el
  mismo semáforo, pero como fotografía diaria en vez de aviso puntual.

## Arquitectura
```
bottrading/
  models.py            # Level, Indicators
  indicators.py         # SMA/EMA/RSI(Wilder)/MACD + clasificación de avisos + entry_signal
  notifier.py           # Telegram (+ notificación Mac opcional)
  engine.py             # watchlist, sondeo, cruces de nivel, señal proactiva, resumen diario, persistencia
  commands.py           # comandos de Telegram
  providers/
    crypto.py            # CoinGecko (precio + histórico + búsqueda de id)
    stocks.py             # Yahoo Finance chart endpoint (precio + histórico)
    fx.py                 # tipo de cambio USD→EUR (frankfurter.app, con caché)
run.py                  # modo config / nube
bot.py                  # modo bot interactivo
watches.yaml            # watchlist (versionada, sin secretos) — 30 activos
```

## Límites honestos
- Los niveles de `watches.yaml` son una **foto fija** del momento en que se
  definieron (23-ago-2026 los primeros 12, 10/11-sept-2026 los últimos 13) —
  el mercado se mueve y hay que revisarlos de vez en cuando (o mandar
  `/analisis SYMBOL` para ver dónde está el precio ahora respecto a sus
  propias medias, no contra un número que ya quedó viejo).
- Los indicadores (RSI/SMA/MACD) se recalculan con caché de 4h
  (`history_ttl`), no en cada sondeo — el precio sí es en vivo cada vez. La
  señal proactiva de cada 30 min reutiliza ese mismo caché (no fuerza una
  llamada nueva a la API cada vez), así que en el peor caso puede tardar
  hasta 4h en reflejar un movimiento de RSI muy reciente.
- Los umbrales de `entry_signal` (RSI≤30, RSI 50-65 + MACD positivo...) son
  heurísticas razonables, no una fórmula infalible — pueden dar falsos
  positivos igual que cualquier indicador técnico.
- Esto es apoyo a la decisión, no un sistema de trading automático: **no
  compra ni vende nada por ti**, solo avisa. No es consejo financiero.

Licencia MIT. Uso personal y responsable.
