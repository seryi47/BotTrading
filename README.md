# BotTrading 📈🔔

Vigila el precio de BTC, ETH, Mastercard, Oracle y Alpha and Omega Semiconductor
(o lo que tú le añadas) y te avisa por Telegram en cuanto el precio **cruza un
nivel** — con lectura técnica (RSI, medias, tendencia) incluida en el propio
aviso, no solo el número desnudo. Misma arquitectura que
[BotViajes](../BotViajes), adaptada de "avisar cuando hay billete" a "avisar
cuando el precio hace lo que llevamos vigilando".

- Precios en vivo: CoinGecko (cripto) y Yahoo Finance (acciones), sin API key.
- Cada aviso lleva el precio en USD **y en euros** (conversión con el tipo de
  cambio del día — el mercado real cotiza en USD, ver nota en `/ayuda`).
- Los niveles de la watchlist inicial (`watches.yaml`) son los que fuimos
  calculando a mano: soportes/resistencias, SMA20/50/200, y la regla de "no
  perseguir con RSI en sobrecompra" aplicada automáticamente en cada aviso.
- Resumen diario por Telegram (hora configurable) con el estado de todos los
  activos, aunque no haya saltado ningún nivel.
- Añade tus propios niveles a mano desde Telegram con `/vigilar`, en cualquier
  cripto o acción, no solo las 5 iniciales.
- Se para y se reanuda desde Telegram (`/pausa`, `/seguir`, `/apagar`).

> A diferencia de BotViajes, aquí **no hay aviso repetido en bucle**: cada
> nivel avisa una vez al cruzarlo, no cada pocos segundos mientras se cumpla
> — un precio no desaparece como un asiento de tren, así que machacar Telegram
> cada 10 s no aporta nada, solo satura.

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

### En la nube 24/7 sin tarjeta (GitHub Actions)
Igual que BotViajes: `.github/workflows/vigilar.yml` sondea en bucle en los
servidores de GitHub, gratis, con repo **público** (los secrets siguen siendo
privados). Configura en *Settings → Secrets and variables → Actions*:
`TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. La watchlist que vigila es
`watches.yaml` (versionado); edítala y haz `git push` para cambiarla.

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
  precio, máximos/mínimos de 52 semanas, niveles psicológicos.
- `ma: sma20|sma50|sma200` — una **media móvil en vivo**: se recalcula en
  cada sondeo con `indicators.resolve_level_price()`, no se queda congelada
  en el número que tenía el día que se definió. Úsalo siempre que el nivel
  sea conceptualmente "cuando recupere/pierda tal media" — si se pusiera
  como precio fijo, en unas semanas ese número ya no coincidiría con dónde
  está esa media de verdad. `/vigilar SYMBOL; accion; sma200; sube; nota`
  también acepta este tipo desde Telegram.

## Cómo decide "cruce de nivel"
Cada activo guarda el último precio conocido (`last_price`). En cada sondeo
compara el precio nuevo contra cada nivel:
- `cae`: avisa si el precio **estaba por encima** del nivel y ahora está
  **en o por debajo**.
- `sube`: avisa si el precio **estaba por debajo** y ahora está **en o por
  encima**.

Así solo avisa en el cruce real, no cada vez que el precio simplemente sigue
por debajo/encima de un nivel ya cruzado antes.

## Cómo decide "es buena zona o no" (`indicators.classify_alert`)
La misma regla que aplicamos a mano en el chat:
- Toca un **soporte** (`cae`) con RSI ya enfriado (≤45) → 🟢 posible zona de
  compra. Con RSI todavía alto → 🟡 esperar confirmación, el nivel solo no
  basta.
- Rompe una **resistencia** (`sube`) con RSI en sobrecompra extrema (≥75) →
  🔴 no perseguir. Con margen de RSI → 🟢 continuación con más credibilidad.

## Arquitectura
```
bottrading/
  models.py            # Level, Indicators
  indicators.py         # SMA/EMA/RSI(Wilder)/MACD + clasificación de aviso
  notifier.py           # Telegram (+ notificación Mac opcional)
  engine.py             # watchlist, sondeo, cruces de nivel, resumen diario, persistencia
  commands.py           # comandos de Telegram
  providers/
    crypto.py            # CoinGecko (precio + histórico + búsqueda de id)
    stocks.py             # Yahoo Finance chart endpoint (precio + histórico)
    fx.py                 # tipo de cambio USD→EUR (frankfurter.app, con caché)
run.py                  # modo config / nube
bot.py                  # modo bot interactivo
watches.yaml            # watchlist inicial (versionada, sin secretos)
```

## Límites honestos
- Los niveles de `watches.yaml` son una **foto fija** del 23-ago-2026 — el
  mercado se mueve y hay que revisarlos de vez en cuando (o mandar
  `/analisis SYMBOL` para ver dónde está el precio ahora respecto a sus
  propias medias, no contra un número que ya quedó viejo).
- Los indicadores se recalculan con caché de 4h (`history_ttl`), no en cada
  sondeo — el precio sí es en vivo cada vez.
- Esto es apoyo a la decisión, no un sistema de trading automático: **no
  compra ni vende nada por ti**, solo avisa. No es consejo financiero.

Licencia MIT. Uso personal y responsable.
