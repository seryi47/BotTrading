# Seguimiento a fondo de acciones — 26/27-sept-2026

Documento de referencia con todo lo investigado sobre las acciones añadidas al
bot ese fin de semana: las diez que sigue de cerca Isaac Davydov dentro de su
comunidad de pago (ver [ISAAC_DAVYDOV_METODO.md](ISAAC_DAVYDOV_METODO.md),
sección 5.4) más las mejores candidatas del segundo barrido de "empresas a
punto de cruzar a beneficio real". Para cada una: qué hace la empresa, precio
y valoración del cierre del viernes 25-sept-2026, actividad real de insiders,
movimientos recientes de precio objetivo de analistas (con fecha), riesgos
concretos, y los niveles técnicos que se han metido en `watches.yaml`.

Metodología: precios y medias móviles calculados en vivo con el mismo
proveedor que usa el bot (endpoint de gráficos de Yahoo Finance, 1 año de
cierres diarios). El resto (noticias, insiders, objetivos de analistas) viene
de múltiples búsquedas web citadas en cada apartado — nada inventado; donde
una fuente no tenía el dato, se dice explícitamente.

## Ranking de convicción (de más a menos, con todo lo aprendido)

1. **Madrigal (MDGL)** — la más sólida.
2. **Amazon (AMZN)** — ya en el bot desde antes.
3. **Cipher Digital (CIFR)**
4. **Cava Group (CAVA)**
5. **Oscar Health (OSCR)**
6. **Zeta Global (ZETA)**
7. **HIVE Digital (HIVE)**
8. **Travere (TVTX)**
9. **Cohu (COHU)**
10. **Meta (META)** — ya en el bot desde antes.
11. **Ryerson (RYZ)**
12. **Axsome (AXSM)**
13. **Netflix (NFLX)**
14. **Phathom (PHAT)** — rebajada tras el profit warning de julio.
15. **Novo Nordisk (NVO)** — la más consistentemente negativa.
16. **Lemonade (LMND)** — ya en el bot desde antes, niveles corregidos el 26-sept.
17. **AeroVironment (AVAV)** — se investigó a fondo pero se bajó de prioridad por venta de insiders sin ninguna compra.

---

## Madrigal Pharmaceuticals (MDGL)

**Qué hace:** biotecnológica centrada en el hígado graso avanzado (MASH). Su
fármaco Rezdiffra fue el primer y único aprobado por la FDA para esta
enfermedad (2024), activando un receptor de hormona tiroidea en el hígado
para reducir grasa e inflamación.

**Precio (cierre 25-sept):** 516,56 $ · Capitalización: 11.930 M$ · Rango 52
semanas: 412,35 – 602,83 $ (Yahoo Finance) · Ingresos TTM +149% · Aún no
rentable (pérdida neta -325M$ TTM) pero con caja de 839M$.

**Analistas:** consenso "Strong Buy", objetivo medio 682$ (+32%). Goldman
Sachs inició cobertura el 24-sept ($704) y Citi el 23-sept ($725) — entradas
muy recientes, no de hace meses. Barclays con el objetivo más alto, 962$.

**Insiders:** solo ventas rutinarias (ejercicio de opciones + retención
fiscal, planes 10b5-1), nada oportunista. Corto interés alto: 16,3% del
free float — mucha apuesta bajista que puede generar movimientos fuertes al
alza si se equivocan.

**Riesgo real:** dependencia de un único producto; Novo Nordisk ya tiene su
Wegovy aprobado para la misma enfermedad, Eli Lilly y Roche podrían entrar
después de 2028. Patente en EEUU protegida hasta 2045.

**Niveles en el bot:** sma200 (≈512$) soporte de fondo · sma50 (≈527$)
resistencia inmediata · 602,83$ máximo de 52 semanas.

---

## Cipher Digital (CIFR, antes Cipher Mining)

**Qué hace:** minera de bitcoin reconvertida en infraestructura de centros de
datos para IA/HPC (alquiler de capacidad de cómputo a hyperscalers). Cambió
de nombre en feb-2026 para reflejar el pivote.

**Precio (cierre 25-sept):** 17,73 $ · Rango 52 semanas: 11,47 – 29,18 $.

**Contratos reales:** Barber Lake (con Fluidstack/Google) va DOS MESES
adelantado sobre plazo, contrato ampliado el 25-sept a más de 9.000M$ de
ingresos contratados; Black Pearl (con AWS) sin retrasos. El 8-sept subió un
8% mientras Bitcoin bajaba — primera señal clara de desacople de la
correlación tradicional con BTC.

**Analistas:** Morgan Stanley subió el objetivo a 54$ desde 43,50$ a finales
de septiembre. Consenso "Strong Buy", objetivo agregado ~30$.

**Insiders:** solo ventas (CEO Tyler Page, ~5,5M$ en el año vía plan 10b5-1;
accionista mayoritario Holding LTD V3 vendió ~78,5M$ en 6 meses). Ninguna
compra.

**Riesgo:** capex masivo (gasoductos de gas natural, generación on-site) que
necesita financiarse sin diluir en exceso ni deteriorar el balance.

**Niveles en el bot:** sma50 (≈18,2$) resistencia · sma20 (≈16,9$) soporte
corto · 19,33$ (máximo de septiembre) · 14$ (suelo de la consolidación).

---

## AeroVironment (AVAV)

**Qué hace:** fabricante de drones militares (Switchblade, usado en combate
real en Ucrania) y, tras comprar BlueHalo, también sistemas láser
anti-drones (LOCUST), espacio y ciberseguridad.

**Precio (cierre 25-sept):** 152,05 $ · Rango 52 semanas: 136,68 – 409,83 $
(cae un 49,6% en el año).

**Contratos reales:** 464,8M$ del Ejército de EEUU por el sistema LOCUST
(2-sept), primer pedido internacional del mismo sistema (8-sept), acuerdo
para fabricar Switchblade en Ucrania.

**El "pero" importante:** margen bruto cayó del 39% al 22% por la integración
de BlueHalo; pérdida GAAP de 265,1M$ en el año fiscal, en gran parte por un
cargo contable de 240,7M$ (deterioro de fondo de comercio), no por quemar
caja de verdad — el beneficio ajustado guiado es positivo (2,75-3,10$/acción).

**Analistas:** BofA bajó el objetivo a 185$ desde 225$ (21-sept), Goldman
Sachs a 285$ desde 326$ (17-sept), Jefferies a 204$ desde 229$ (16-sept) —
tres recortes la misma semana pese a las buenas noticias de contratos.

**Insiders:** 3,2M$ vendidos en 12 meses, CERO compras. Señal de cautela real
que hizo bajar esta acción de prioridad pese a los buenos fundamentales.

**Niveles en el bot:** sma50 (≈158,7$) resistencia, primera señal de
estabilización si se recupera · 136,68$ mínimo de 52 semanas · 185$ (objetivo
de BofA tras el recorte).

---

## Cava Group (CAVA)

**Qué hace:** cadena de restaurantes de comida mediterránea rápida-casual, en
expansión agresiva (500 locales a finales de sept-2026), a menudo comparada
con Chipotle.

**Precio (cierre 25-sept):** 51,58 $ · Rango 52 semanas: 43,59 – 97,39 $.

**El negocio no se ha roto:** ventas comparables +9% (superando consenso),
tráfico +5,3%, ingresos +31% en el último trimestre. La caída es de
valoración (venía de pagarse a ~90-120x beneficio) y de venta sectorial de
"growth"/restaurantes desde junio-julio, amplificada por el miedo puntual a
un brote de Cyclospora en lechuga (CAVA no estuvo implicada, de hecho superó
a sus comparables en tráfico ese periodo).

**Insiders — señal positiva real:** el COO Douglas Thompson ha comprado
acciones TRES veces este año (mayo, junio y 7-sept, esta última por 432.000$).

**Analistas:** JPMorgan bajó el objetivo a 80$ desde 85$ (18-sept), pero
Seaport inició cobertura de compra el 15-sept y Telsey la reiteró el mismo
día. Consenso "Moderate Buy" con objetivo ~85-96$.

**Técnico:** RSI en zona de sobreventa clara (~33,6), cruce de medias
bajista confirmado en agosto (death cross).

**Niveles en el bot:** 45,50$ cerca del mínimo de 52 semanas · sma20 (≈56$)
primera resistencia · 56$ nivel citado por analistas.

---

## Oscar Health (OSCR)

**Qué hace:** aseguradora de salud centrada en el mercado individual (ACA) de
EEUU, con tecnología propia de gestión de siniestros.

**Precio (cierre 25-sept):** 29,60 $ · Rango 52 semanas: 10,85 – 33,81 $
(+60% en el año).

**Fundamentales reales mejorando:** ya rentable en GAAP, ratio de
siniestralidad bajado de 91% a 79% en un año, ingresos +43%. En su Investor
Day del 16-sept subió la guía de beneficio operativo 2026 y varias casas le
subieron el objetivo con fuerza (Barclays a 49$, Raymond James a 42$).

**El riesgo estructural, ahora mismo activo:** el shutdown de EEUU se evitó
el 27-sept, pero SIN extender los subsidios sanitarios ampliados de la ACA —
la inscripción ya ha caído un 4,9% y las primas sin subsidio han subido casi
un 20%. Riesgo directo para el negocio de marketplace.

**Insiders — patrón repetido de alarma:** el CEO Mark Bertolini compró 1M de
acciones en abril y vendió 1,24M (~35,7M$) en junio, sin mencionarlo nunca
después en sus propios vídeos de YouTube (ver la biblia de Isaac Davydov).
Ahora, en agosto-septiembre, el presidente/COO Mario Schlosser vendió
~23M$ y el CFO Richard Blackley también vendió, justo en las semanas del
Investor Day que disparó el precio.

**Niveles en el bot:** sma50 (≈30,7$) resistencia inmediata · 26$ soporte
real · 35,40$ objetivo medio de analistas.

---

## Zeta Global (ZETA)

**Qué hace:** plataforma de marketing y datos de consumidor con IA
("omnichannel marketing cloud") para grandes empresas.

**Precio (cierre 25-sept):** 29,45 $ · Rango 52 semanas: 14,55 – 32,68 $.

**Negocio:** cuarto trimestre seguido subiendo su propia previsión de
ingresos/EBITDA (+44% ingresos, +56% EBITDA ajustado en Q2). Ya con beneficio
neto GAAP positivo puntual.

**Antecedente relevante:** en noviembre de 2024, el fondo bajista Culper
Research publicó un informe acusándola de inflar ingresos y prácticas de
datos cuestionables — la acción cayó un 34-37% en un día. Zeta lo refutó y no
hay ataque nuevo activo en 2026, pero el modelo de negocio sigue siendo
vulnerable a este tipo de escrutinio.

**Insiders:** solo ventas; el CEO David Steinberg firmó además un contrato
derivado ("Variable Prepaid Forward") para vender 1 millón de acciones a
futuro — reduce su exposición neta sin ser una venta directa inmediata.

**Analistas:** consenso "Buy", objetivo medio ~31$; revisiones recientes al
alza (B. Riley a 24$, Truist a 42$).

**Niveles en el bot:** sma20 (≈30,7$) resistencia tras el enfriamiento desde
máximos · sma50 (≈27,4$) soporte · 32,68$ máximo de 52 semanas.

---

## HIVE Digital Technologies (HIVE)

**Qué hace:** minera de bitcoin en pivote hacia centros de datos de IA/GPU
cloud, con contratos ya firmados con Bell Canada y Cohere.

**Precio (cierre 25-sept):** 3,16 $ · Rango 52 semanas: 1,75 – 6,96 $ (-60%
desde el máximo).

**Lo real:** más de 600M$ en contratos de GPU cloud acumulados en el año,
ARR contratado ~110M$. Bitcoin repuntando (~84.600$) y hashprice +22%,
viento de cola genuino para márgenes de minería.

**El riesgo que no está en precio:** el 25-sept (hace 2 días) escaló
formalmente su disputa fiscal con Suecia (reclasificación de sus filiales
como "auto-minería" en vez de servicio gravable) a la Comisión Europea —
señal de que el proceso durará años, no meses, y si Suecia gana sienta
precedente para todo el sector en la UE.

**Insiders:** sin patrón de venta preocupante, solo compensación normal
(RSUs, ejercicios).

**Niveles en el bot:** sma50 (≈2,97$) soporte cercano · 3,315$ resistencia
(zona de la media de 100 sesiones) · 1,75$ mínimo de 52 semanas.

---

## Travere Therapeutics (TVTX)

**Qué hace:** biotecnológica centrada en enfermedades renales raras. Su
fármaco Filspari (sparsentan) es el único aprobado para FSGS, una
enfermedad renal sin competencia directa.

**Precio (cierre 25-sept):** 59,44 $ · Rango 52 semanas: 23,90 – 67,52 $
(+143% en el año).

**Negocio:** Filspari +96% interanual, la empresa casi en punto de
equilibrio real (pérdida no-GAAP de solo 9M$).

**La señal de alarma que hace bajar la convicción:** el CEO Eric Dubé vendió
~25,4M$ en acciones entre el 15 y 17-sept, muy cerca de máximos, y CUATRO
DÍAS DESPUÉS (21-sept) anunció que dejaba el cargo por motivos de salud/
familia. Coincidencia temporal a vigilar, aunque bajo plan 10b5-1
preestablecido, no venta discrecional de última hora.

**Analistas:** Stifel subió el objetivo a 62$ desde 43$ pero mantuvo "Hold",
no "Buy" — sube el número sin subir la convicción.

**Niveles en el bot:** sma50 (≈62$) resistencia · sma200 (≈44,4$) soporte de
fondo · 67,52$ máximo de 52 semanas.

---

## Cohu Inc (COHU)

**Qué hace:** fabricante de equipos para probar (test) semiconductores tras
fabricarlos, con fuerte demanda actual ligada a chips de IA/HPC.

**Precio (cierre 25-sept):** 67,00 $ · Rango 52 semanas: 18,74 – 73,91 $
(+236% en 12 meses).

**Negocio real, no solo hype:** pedidos de computación IA/HPC +150%
interanual, pedido puntual de 26M$ de un cliente en julio, pipeline de
clientes HPC ampliado a ~850M$, guía anual subida a +35%.

**El riesgo:** el CEO Luis Muller vendió 3,3M$ el 21-sept cerca de máximos
históricos (sin ninguna compra que lo compense); riesgo real de dilución por
bonos convertibles cuya cobertura ("capped call") protegía solo hasta 41$, ya
ampliamente superados; 10 clientes representan el 63% de sus pedidos.

**Analistas:** múltiples subidas recientes — Needham a 65$, TD Cowen a 80$,
B. Riley a 69$. Consenso "Strong Buy", objetivo medio 70,88$.

**Niveles en el bot:** 73,91$ máximo de 52 semanas · sma20 (≈54,3$) soporte
real tras el rally · 60$ zona de consolidación previa.

---

## Ryerson Holding (RYZ, antes RYI)

**Qué hace:** distribuidor de acero y metales (centro de servicio), acaba de
fusionarse con Olympic Steel (cerrada 13-feb-2026).

**Precio (cierre 25-sept):** 23,85 $ · Rango 52 semanas: 19,86 – 31,03 $.

**Lo bueno:** sinergias de la fusión corriendo por delante de lo prometido
(52-56M$ de ritmo anualizado vs objetivo de 40M$).

**El riesgo real:** apalancamiento saltó de 3,1x a 5,1x en un solo trimestre
por la deuda combinada de la fusión — agresivo para un negocio cíclico.
Cobertura de analistas casi inexistente y con datos que ni coinciden entre
plataformas.

**Insiders:** solo ventas rutinarias, sin compras.

**Niveles en el bot:** sma20 (≈24,9$) primera resistencia · sma200 (≈26,3$)
resistencia de fondo · 19,86$ mínimo de 52 semanas.

---

## Axsome Therapeutics (AXSM)

**Qué hace:** biotecnológica de fármacos para el sistema nervioso central
(depresión, narcolepsia, agitación por Alzheimer).

**Precio (cierre 25-sept):** 195,09 $ · Rango 52 semanas: 116,76 – 255,17 $.

**La contradicción con la tesis original:** ingresos +46% (fuerte), pero la
PÉRDIDA NETA AUMENTÓ interanualmente (51,3M$ vs 48M$) por el gasto comercial
del lanzamiento de una nueva indicación — justo lo contrario de "a punto de
cruzar a beneficio real". 82% de los ingresos dependen de un solo producto
(Auvelity) en una indicación con solo 3 meses de vida comercial.

**Analistas:** Morgan Stanley bajó el objetivo a 247$ desde 251$ en
septiembre — primera voz cautelosa tras meses de solo subidas.

**Niveles en el bot:** sma200 (≈198,9$) soporte inmediato · sma20 (≈206,2$)
resistencia · 255,17$ máximo de 52 semanas.

---

## Netflix (NFLX)

**Qué hace:** plataforma de streaming de vídeo, con negocio publicitario en
fuerte expansión.

**Precio (cierre 25-sept):** 71,15 $ · Rango 52 semanas: 67,60 – 124,14 $
(peor año desde 2022).

**Fundamentales siguen creciendo:** ingresos +16%, beneficio +33%,
publicidad camino de duplicarse este año — la caída es sobre todo miedo a
que YouTube le esté comiendo audiencia (horas vistas por suscriptor -8%
interanual ajustado).

**Insiders — solo ventas:** Reed Hastings vendió ~33M$ en junio y ~34M$ en
mayo; el co-CEO Ted Sarandos también vendió; un consejero volvió a vender el
8-sept. Ninguna compra.

**Analistas divididos:** Wells Fargo bajó a "vender" con objetivo de 57$ el
18-sept citando el deterioro de engagement, pero Evercore había subido a
110$ apenas días antes. Consenso amplio sigue en "Buy", objetivo medio 93$.

**Catalizador real:** resultados el 20-oct-2026.

**Niveles en el bot:** sma20 (≈76,7$) resistencia a reconquistar · 67,60$
cerca del mínimo de 52 semanas · 92,93$ objetivo medio de analistas.

---

## Phathom Pharmaceuticals (PHAT)

**Qué hace:** biotecnológica con Voquezna (vonoprazan), fármaco para reflujo
gastroesofágico (GERD) grave, licenciado de Takeda.

**Precio (cierre 25-sept):** 7,30 $ · Rango 52 semanas: 6,99 – 18,08 $ (-60%
desde el máximo).

**Rebajada de prioridad tras este hallazgo:** en julio la propia empresa
recortó su guía de ingresos anuales citando fricciones reales de
autorización previa de las aseguradoras — la acción cayó un 22% en un día,
su peor sesión desde 2024. Desde entonces varias casas han seguido bajando
el objetivo (Craig-Hallum, Raymond James, Barclays) hasta que Leerink inició
cobertura neutral, no de compra, el 9-sept.

**Dilución cara:** ampliación de capital de enero-2026 a 16$/acción — más
del doble del precio actual, esos inversores están hoy en pérdidas de más
del 50%. Vencimiento de deuda relevante en 2027.

**Lo único a favor:** exclusividad regulatoria de la FDA hasta 2032 (cubre
el riesgo de genéricos pese a que la patente de sustancia es más débil), y
algunas compras de insiders en los últimos 24 meses.

**Niveles en el bot:** sma20 (≈8,4$) primera resistencia · 6,99$ cerca del
mínimo de 52 semanas · 16$ precio de la ampliación de capital de enero.

---

## Novo Nordisk (NVO)

**Qué hace:** farmacéutica danesa, líder histórico en diabetes/obesidad
(Ozempic, Wegovy), ahora perdiendo cuota frente a Eli Lilly.

**Precio (cierre 25-sept):** 38,80 $ · Rango 52 semanas: 35,29 – 63,98 $
(-34% en el año).

**Deterioro real, no solo miedo:** su fármaco de nueva generación CagriSema
perdió el ensayo clínico directo frente al Zepbound de Eli Lilly
(feb-2026), ha recortado su propia previsión de crecimiento, despedido a
9.000 empleados y cambiado de CEO con medio consejo destituido.

**Sin ningún contrapeso:** el Capital Markets Day del 24-sept (que debía
reconstruir confianza) fue recibido con una caída del 8% por falta de
sustancia. Deutsche Bank bajó el objetivo dos días antes. Ninguna subida de
objetivo reciente detectada, ninguna compra de insider.

**Niveles en el bot:** 35,29$ cerca del mínimo de 52 semanas · sma20
(≈43,1$) primera resistencia · 46,39$ objetivo medio de analistas.

---

## Nota final sobre Meta y Amazon (ya en el bot desde antes)

**Meta:** subió un 37% en septiembre (mejor mes desde 2013) por el éxito de
su asistente de IA "Muse" y el cierre de su gran frente legal (17.100M$ por
prácticas con menores). Cotiza en máximos de 52 semanas — el consenso de
analistas (objetivo medio ~780$) ya está prácticamente al mismo nivel que el
precio, señal de que el mercado se adelantó a los propios analistas.

**Amazon:** más equilibrada — AWS acelerando al 37% (su mejor ritmo en 18
trimestres), objetivo de analistas un 32% por encima del precio actual (la
mayor brecha de todo este listado). Jeff Bezos anunció un plan para vender
hasta 4.800M$ en acciones, la venta de insider más grande, en tamaño
absoluto, de todo este listado, aunque programada. El litigio antitrust de
la FTC sigue abierto, con juicio aplazado a feb-2027.
