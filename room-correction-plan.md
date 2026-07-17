# Plan: corrección de sala estilo Dirac/miniDSP en el streamer UXX

> **FASE 0 COMPLETADA (2026-07-17): pipeline entero validado contra la API REAL de REW**
> (5.40 Beta 130, API 0.9.5, en el Mac de Albert, localhost:4735 — OJO: solo escucha en
> localhost; el orquestador debe correr EN el Mac, el UXX solo reproduce el sweep).
> Demostrado end-to-end con sala SINTÉTICA (script: `~/nada/rew-pipeline-test.py`; spec
> completa: `~/nada/rew-openapi-0.9.5.json`, 378 endpoints):
> import IR ×2 posiciones → Vector average → equaliser **CamillaDSP nativo** (¡REW genera
> filtros en formato CamillaDSP directamente — el paso de conversión desaparece!) →
> target settings + Calculate target level → match-target-settings (rango/límites de boost)
> → **Match target** (encontró EXACTAMENTE los modos plantados: 43.36/86.05/176.28 Hz vs
> 43/86/176 sintéticos) → lectura de filtros (fc/gain/Q) → **Generate predicted measurement**
> → **Generate RT60** (params filterOrder/octaveFrac) + lectura por bandas
> (`?octaveFrac=3`: EDT/T20/T30/Topt/C50/C80/D50 → columna decay de la tabla de modos).
> Los 4 amarillos de la auditoría: TODOS resueltos (predicted = comando "Generate predicted
> measurement" + `/measurements/{id}/eq/frequency-response`; RT60 legible; input-cal ya
> tiene GET; spl-meter endpoints presentes). Gotchas: `/measurements` devuelve DICT
> {indice:objeto}, no lista; `Generate RT60` exige parameters; el GET de rt60 necesita
> `octaveFrac` igual al generado; modo blocking (`/application/blocking` true) hace los
> comandos síncronos = orquestación simple. **Falta solo lo que requiere micrófono**:
> sweeps reales (y decisión REW Pro para automatizarlos), house-curves (trivial), alignment
> L/R (misma familia de API). Las mediciones sintéticas quedaron en el REW de Albert para
> que las vea (Synthetic pos 1/2, Vector average, EQ Vector average).
> ⚠️ GOTCHA post-demo: poco después REW lanzó `ArrayIndexOutOfBoundsException` y pidió
> reiniciar — REW es BETA y nuestros IR sintéticos son un caso límite (impulso perfecto con
> energía hasta DC; el RT60 llegó a devolver una banda "0.0 Hz"). Lecciones para la fase
> real: (1) generar sintéticos más fisiológicos (high-pass ~10 Hz, algo de ruido de fondo);
> (2) en sesiones REALES guardar el .mdat a menudo (comando "Save all" existe por API);
> (3) tras un crash, reiniciar REW con -api y seguir — la API no guarda estado propio.

> **ENSAYO GENERAL DE MEDICIÓN COMPLETADO (2026-07-17, micro webcam C920 sin calibrar):**
> la coreografía completa funcionó A LA PRIMERA — Generator→"Meas. Sweep"→WAV con timing
> reference → scp al UXX → disparo retardado (`sleep 30 && pw-play ~/sweeps/sweep.wav`,
> cadena en bypass) → Albert pulsa Start (GUI, Pro capa el resto) → REW cazó la referencia
> acústica y midió 20-20k. Análisis por API de la SALA REAL (solo fiable en graves/medios
> por el micro): **modos del despacho: +11.6 dB @ 64 Hz, +9.2 @ 81 Hz, +9.6 @ 128 Hz**
> (128≈2×64: armónico del modo principal) y **valles -9 dB @ 263/281 Hz** (SBIR/mesa);
> banda 60-120 Hz +5 dB de boom global; <60 Hz cae (JVC pequeños). El día del UMIK:
> repetir esta MISMA coreografía ×9 posiciones y correr el pipeline ya validado.
> Detalles de campo: REW espera la referencia sin prisa (30 s de countdown sobraron);
> el WAV del Generator salió F32 12.3 s; medición nombrada por Albert en la GUI.
> **SESIÓN DE FÍSICA COMPLETADA (2026-07-17, mismo mic C920 fijo → comparaciones relativas
> válidas). Resultados A/B/C:** pegados vs separados(+8cm→~14cm de pared) vs separados+
> calcetines en puertos: separación → nulo SBIR de −8.9→−5.9 dB (gratis, sin perder graves);
> calcetines → pico 64 Hz −3.6 dB y boom 60-120 de +5.5→+2.4 (graves mucho más uniformes,
> rugosidad 5.9→5.1) A CAMBIO de −5 dB en 40-60 Hz (alineamiento sellado). **Decisión
> provisional: separados + calcetines + Loudness Ambient** para devolver extensión;
> reevaluar de oído unos días y confirmar el día del UMIK (opción término medio: puerto
> semi-tapado). Mediciones en REW: 1=pegados, 2=pos2-sin-tapones, 3=pos2-con-tapones.
> **Contexto físico (confirmado por Albert post-medición): los JVC estaban CASI PEGADOS a la
> pared y tienen PUERTO REFLEX TRASERO.** Cuadra todo: valles 263/281 Hz = SBIR pared trasera
> (d≈343/(4×270)≈32 cm ≈ fondo del altavoz + hueco); boom 60-120 = refuerzo de contorno +
> puerto descargando contra pared (pico 64 Hz ~ sintonía típica del puerto). PARA LA SESIÓN
> UMIK: (1) probar TAPONES de puerto (espuma) con sweep A/B antes de corregir — física antes
> que EQ; (2) intentar ganar 5-10 cm de pared si es posible (mueve/suaviza el nulo SBIR);
> (3) los nulos SBIR NO se corrigen con EQ (ya es regla del plan); los picos 64/81/128 sí.

> **Estado original: PENDIENTE** (visión acordada 2026-07-03: "emular miniDSP + Dirac — corrección de
> sala en serio; construyendo el streamer perfecto").
> Este doc permite a una sesión futura de Claude ejecutarlo sin releer la conversación.
> Sala objetivo: **Despacho** — UXX ($STREAMER_IP) → SMSL A50 Pro (USB, 16/48 máx) → JVC SP-UXJ60.

## Qué emula a qué

| Comercial | Nuestro equivalente | Coste |
|---|---|---|
| Micrófono Dirac/miniDSP | **miniDSP UMIK-1** (USB, con fichero de calibración) | ~110 € — ÚNICA compra |
| Medición Dirac (sweeps multipunto) | **REW** (Room EQ Wizard, gratis, en el Mac) | 0 |
| Motor de corrección Dirac (FIR fase mixta) | **DRC-FIR** (Denis Sbragion) — corrección magnitud+fase, ventanas psicoacústicas | 0 |
| Caja miniDSP (convolución en vivo) | **CamillaDSP** en el UXX (o convolver nativo de PipeWire filter-chain como plan B) | 0 |

## Arquitectura en el UXX

```
MPD / spotifyd / radio → PipeWire → [sink virtual "DSP"] → CamillaDSP (convolución FIR estéreo)
                                                            → sink real A50 Pro (S16/48k + dither)
```
- **Conmutable**: se mantienen los DOS caminos — "directo" (bit-perfect, el actual) y "DSP"
  (corregido). Alternar = cambiar default sink (`wpctl set-default`). Añadir acción
  `eq on|off|status` a `~/.local/bin/audioctl` y a la API `:8080` (allowlist).
- Con DSP activo, fijar el reloj a **48 kHz** (un solo juego de filtros FIR; el remuestreo
  44.1→48 del material CD lo hace PipeWire — con corrección activa el bit-perfect ya no aplica).
  Alternativa: generar FIR también a 44.1k y que CamillaDSP cambie de config por rate.
- **Headroom**: los filtros DRC se normalizan con ganancia negativa (típico −3..−8 dB) para
  que ningún boost clipee a 0 dBFS. El volumen sigue siendo analógico en el ampli → sin coste real.
- **Dither**: activar `dither.method` (p.ej. `wannamaker3`) en la reconversión a S16 del
  camino DSP (hoy está a none porque no procesamos).
- CPU: convolución FIR estéreo 48k (~65k taps) = pocos % del N3350. Verificado viable.

## ARQUITECTURA v2 (diseño 2026-07-08): orquestación por REW API, aprendiendo de Dirac y Audyssey

### La API de REW (la pieza que lo automatiza todo)
REW incluye un **servidor HTTP** (beta): se arranca con `roomeqwizard -api` (puerto **4735**)
y expone su funcionalidad por REST con **documentación OpenAPI en `http://localhost:4735/docs`**.
Endpoints conocidos: mediciones, promedios, `/eq/*` (house curves, "Generate target measurement",
"Match Response to Target" = su auto-EQ), export de filtros/IR. **Paso 0 de la implementación:
levantar la API y volcar el OpenAPI para mapear los endpoints exactos** (es beta: verificar, no asumir).

### Qué copiamos de cada uno
**De Dirac Live:**
1. **Medición multipunto** (9-13 posiciones en rejilla ~60×40cm alrededor del punto de escucha),
   promediadas → corregir lo CONSISTENTE entre posiciones, no la foto de un punto.
2. **Corrección de fase mixta** (FIR): corrige magnitud Y dominio temporal (impulso) → Tier 2 (DRC-FIR).
3. **Target editable con default sensato**: tilt descendente suave; límites de corrección
   configurables (p.ej. corregir fuerte <500 Hz, suave arriba).
4. **No rellenar nulos**: los cancelamientos de sala no se corrigen con EQ (pozo sin fondo) —
   el auto-EQ debe limitar boosts (max +3..4 dB).

**De Audyssey MultEQ XT32:**
1. **Curva "Reference" no plana**: tilt + **dip de compensación de medios (~2 kHz, ~-2 dB)** +
   caída suave de agudos — el "flat anecoico" suena áspero en sala; Reference suena "bien".
2. **Ponderación de posiciones**: la posición principal (silla del escritorio) pesa más.
3. **⭐ Dynamic EQ (compensación de sonoridad)** — LA idea más valiosa para Albert: escucha a
   volumen bajo/ambiental, donde el oído pierde graves y agudos (curvas isofónicas ISO 226).
   Audyssey lo liga al mando de volumen; NOSOTROS NO PODEMOS (volumen analógico en el ampli,
   el software no sabe el SPL) → versión manual: **selector "Loudness: off/low/ambient"** en
   la UI /dsp que suma un tilt isofónico encima de la corrección. Manual pero honesto.
4. **UX de wizard**: pipeline automático de principio a fin, cero conocimiento requerido.

### Arquitectura
```
Mac (REW + API :4735 + UMIK-1 USB)          UXX (reproducción + DSP)
        │  orquestador (script python) ──────────┤
        │  1. exporta sweep WAV ──────────────→ MPD/pw-play lo reproduce (cadena REAL, bit-perfect)
        │  2. REW captura via UMIK (timing ref acústica) — ×9-13 posiciones (mover mic entre pasos)
        │  3. promedio ponderado + target elegido (Harman/Reference/Flat/Custom)
        │  4a. Tier 1: REW auto-EQ → biquads paramétricos → sink filter-chain "dsp_room"  ("Audyssey-lite")
        │  4b. Tier 2: DRC-FIR fase mixta → convolver/CamillaDSP                           ("Dirac-like")
        │  5. aplica → re-mide 1 sweep → overlay vs target → informe antes/después
```
- **Sweep por fichero** (no AirPlay/red): se mide la cadena real MPD→PipeWire→DAC→ampli→JVC
  sin resampleos de transporte; la timing reference acústica de REW alinea.
- **Targets como ficheros** versionados en `~/.config/room-correction/targets/`:
  `harman-room.txt` (tilt ~-1dB/oct + shelf graves), `reference.txt` (estilo Audyssey: tilt
  + dip 2k + rolloff HF), `flat.txt`, `custom.txt` (la house curve de Albert cuando la tenga).
- **Modo "room" = 4º modo de la capa DSP** existente (bypass/eq/valve/**room**): sink
  `dsp_room` propio; el conmutador y la UI /dsp ya saben hacer esto. El EQ manual de 10
  bandas queda como está (juguete/manual); room correction va en su sink aparte.
- **UI**: botón "Room" + selector de target + "measured <fecha>, ±X dB" + toggle Loudness.

### Recursos previos REUTILIZABLES (proyecto ReverbBob, mayo 2026)
- **Spec completa de la REW API ya investigada**: `~/.claude/projects/-Users-albert-REW/memory/project_rew_api.md`
  — LEERLA al implementar (endpoints exactos: `/measure/playback-mode` file-playback,
  `/measure/file-playback-stimulus`, `/measurements/process-measurements` (vector/RMS average,
  time align), `/eq/house-curve` + `/eq/match-target-settings` + `/measurements/:id/filters`,
  `/import/sweep-recordings`, `/roomsim/*`, subscripciones de progreso, modo blocking).
- ⚠️ **REW Pro (de pago) hace falta SOLO para disparar sweeps automáticos por API**; el resto
  (leer mediciones, promediar, targets, auto-EQ, filtros) es gratis → **Fase 1 semi-auto**
  (el wizard prepara todo y pide "pulsa Measure en REW"; tras cada medición el wizard sigue solo).
  Full-auto = decisión de compra Pro más adelante.
- ReverbBob (agente conversacional de acústica, webchat, perfiles, informes TLDR) queda como
  proyecto comunitario aparte; NUESTRO room-tab es determinista (formularios/pasos, no chat).
  Ideas heredadas: wizard paso a paso, mapa de posiciones de micro, informe con TLDR no-técnico,
  perfil de sala persistente, indicador de conexión REW.

### Qué aplica de Audyssey/Dirac a nuestro 2.0 de escritorio (decidido)
| Función AVR | ¿Aplica al despacho? | Cómo |
|---|---|---|
| Distancias/delays por canal | **SÍ, solo L/R** (1 número): en escritorio el setup suele ser asimétrico | medir L y R por separado con timing reference → delay relativo → CamillaDSP per-channel delay |
| Trim de nivel por canal | **SÍ** (balance L/R en dB) | de las mismas mediciones |
| Crossover / bass management | **NO** (sin subwoofer) — si algún día hay sub, CamillaDSP lo hace | n/a |
| Modos de sala detectados | **SÍ** — y se MUESTRAN (REW los identifica; lista freq/Q/decay en la UI) | de la medición promediada; corrección fuerte <300 Hz |
| Multipunto ponderado | SÍ (9 posiciones rejilla escritorio) | process-measurements |
| Dynamic EQ / loudness | SÍ, manual (off/low/ambient) | tilt ISO-226 en CamillaDSP |
| Fase mixta | Tier 2 (DRC-FIR) | convolver CamillaDSP |

### Backend: pasar el modo "room" a CamillaDSP (decisión de diseño)
El sink `dsp_room` NO será filter-chain sino **CamillaDSP**, porque una sola config suya encadena
TODO lo de arriba: per-channel **delay + gain** + biquads paramétricos + (Tier 2) convolver FIR +
tilt loudness — y tiene **API websocket propia (:1234) con recarga de config en caliente**, ideal
para la UI. PipeWire le entrega audio via sink virtual → CamillaDSP → SMSL. bypass/eq/valve quedan
como están (filter-chain); "room" es el modo serio.
Estado/perfiles en `~/.config/room-correction/` (JSON: sala, posiciones, mediciones UUID,
target activo, delays/trims, fecha, stats antes/después).

### UI: expandir el dashboard /dsp con pestañas
- **Tab "DSP"** = lo actual (modos + EQ 10 bandas + valve).
- **Tab "Room"** (nueva):
  - **Card estado**: corrección ON/OFF (A/B instantáneo vs bypass), "measured <fecha>",
    target activo, "±X dB 20 Hz–20 kHz", botón Wizard.
  - **Card target**: selector Harman / Reference / Flat / Custom + **Loudness off/low/ambient**.
  - **Card alignment**: delay L/R (ms y cm equivalentes) + trim L/R (dB) — medidos, editables.
  - **Card análisis**: lista de **modos detectados** (freq, +dB, decay) + gráfica
    medida/corregida/target (canvas; los datos salen de la API de REW como arrays float).
  - **Card informe**: TLDR no-técnico + enlace al informe completo (heredado de ReverbBob).
- **Wizard** (overlay paso a paso, estilo ReverbBob pero determinista):
  1. Conexión: ¿REW API viva (:4735)? ¿UMIK presente? ¿cal file cargado?
  2. Niveles: ruido rosa + check SPL/input level (evitar clipping).
  3. Medición ×9: **mapa visual de posiciones** (rejilla 3×3 sobre dibujo del escritorio),
     "posición 4/9: 30 cm a la izquierda" → (semi-auto: "pulsa Measure en REW") → tick verde.
  4. Análisis: promedio ponderado, modos detectados, delay/trim L/R.
  5. Target: elegir curva (preview overlay) → generar filtros (auto-EQ REW).
  6. Aplicar a CamillaDSP → re-medir 1 sweep de verificación → antes/después.
  7. Informe + guardar perfil.

### Trazabilidad UI ↔ REW API (auditado 2026-07-09 contra project_rew_api.md)
Cada dato del mock, de dónde sale de verdad:

| Elemento UI (mock) | Fuente real | Estado |
|---|---|---|
| Curva **measured** | `GET /measurements/:id/frequency-response` (Base64 floats, smoothing/ppo) | ✅ directo |
| Curva **target** | `POST /eq/house-curve` (fichero) + `/eq/command` "Generate target measurement" | ✅ directo |
| Curva **corrected** (predicha) | NO listado un endpoint "predicted" → **la computamos nosotros**: measured + respuesta de los biquads (matemática conocida); verificar en Fase 0 si existe endpoint | 🟡 computable |
| **Filtros** del auto-EQ | `/eq/match-target-settings` + `GET /measurements/:id/filters` (freq/gain/Q) → convertir a config CamillaDSP | ✅ directo |
| **Modos detectados** (freq/+dB/Q) | los picos QUE CORRIGE el auto-EQ = su filter list; complementable con análisis propio del IR (`GET /measurements/:id/impulse-response` da el impulso completo) | ✅ derivable |
| **Decay** por modo (ms) | comando "Generate RT60" existe, pero NO está claro cómo LEER el resultado por API → fallback: computarlo nosotros del impulse-response (lo tenemos entero) | 🟡 verificar F0 |
| **Delay L/R** | `/alignment-tool` (delay-a/b, aligned-response, remove-delay) + process-measurements "Cross corr align" | ✅ directo |
| **Trim L/R** | process-measurements "Align SPL" (o comparar niveles de banda ancha nosotros) | ✅ directo |
| **Promedio multipunto** | process-measurements "Vector/RMS/dB average" — ⚠️ SIN pesos por posición → truco: duplicar la medición central en la lista, o promediar nosotros los arrays | 🟡 workaround fácil |
| Wizard **check REW** | cualquier GET (p.ej. `/application`) responde → viva | ✅ directo |
| Wizard **check UMIK** | `/audio/java/*` lista de input devices → buscar "UMIK" | ✅ directo |
| Wizard **check cal file** | `/audio/input-cal` es **PUT only** según el spec → quizá no se puede LEER; verificar en F0 (fallback: la ponemos nosotros por PUT y listo) | 🟡 verificar F0 |
| Wizard **niveles** (SPL + input) | `/spl-meter/:id/levels` + `/input-levels` (ambos con subscripción en tiempo real) | ✅ directo (confirmar que no es Pro) |
| Disparar **sweep** | `/measure/*` con playback-mode=file-playback — **Pro de pago para automatizarlo** → F1 semi-auto | 🟡 decisión Pro |
| **±X dB accuracy** | la computamos nosotros: desviación RMS del FR verificado vs target en 200 Hz–16 kHz | 🟢 nuestra |
| **Loudness** off/low/ambient | NADA de REW: tilt ISO-226 en config CamillaDSP, puro nuestro | 🟢 nuestra |
| **A/B switch, perfiles, informe** | nuestro (CamillaDSP hot-reload + JSON de perfil + generador de informe) | 🟢 nuestra |

Conclusión de la auditoría: **nada del mock es imposible**; 4 puntos amarillos a verificar en
Fase 0 (todos con fallback computable desde el impulse-response, que la API entrega completo).
- **Fase 0** (30 min): REW con `-api`, volcar OpenAPI, mapear endpoints reales. Decidir REW
  headless vs GUI-con-API (GUI visible ayuda la primera vez).
- **Fase 1**: pipeline semiautomático Tier 1 (medir multipunto asistido por script → auto-EQ
  → dsp_room paramétrico). YA es "Audyssey en casa".
- **Fase 2**: informe antes/después + selector de targets + Loudness manual.
- **Fase 3**: Tier 2 FIR (DRC-FIR + convolver) = fase mixta "Dirac-like". Comparar A/B con Tier 1
  — si Tier 1 ya convence, Tier 2 es opcional.
- **Side-quest** (ya aprobado): curvas secretas E1-E5 y Bass/Treble del A50 Pro (§8).

### Límites honestos (fijados de antemano)
- El A50 Pro capa a 16/48 → toda la corrección vive a 48 kHz. Irrelevante para room correction.
- Los JVC no tienen graves que no tienen: target realista, sin pedir milagros <60 Hz.
- Sin subwoofer no hay integración sub (la joya de XT32 no aplica en el despacho).
- FIR (Tier 2) añade latencia (decenas de ms) — irrelevante para música, no usar para vídeo.

## Flujo de trabajo (pasos)

1. **Comprar/conseguir UMIK-1** (miniDSP; incluye fichero de calibración por nº de serie —
   descargarlo de minidsp.com). Se conecta al **Mac** (REW corre ahí).
2. **REW en el Mac** (`brew install --cask roomeqwizard`; necesita Java). Configurar:
   mic UMIK-1 con su `.cal`, salida = el stream al UXX. Truco para que el sweep suene por
   el A50 Pro: en REW elegir como salida el propio Mac NO vale — reproducir los sweeps
   VIA red: opción simple = generar sweep como WAV en REW y reproducirlo con `mpc` en el
   UXX; opción cómoda = AirPlay no hay; la práctica habitual: llevar el Mac al despacho y
   conectar su salida... NO — mejor: REW soporta "measure through network"? No de serie.
   **Método recomendado**: exportar el sweep de REW a WAV → copiarlo a /mnt/music (vía
   sshfs rw o scp a aslmini) → reproducirlo en bucle con MPD → capturar con REW en modo
   "import sweep response" … Alternativa MÁS SIMPLE y probada por la comunidad:
   instalar REW directamente y usar el UMIK en el Mac mientras el Mac reproduce por
   HTTP→UXX… ⚠️ NOTA PARA CLAUDE: investigar en el momento el método de medición más
   limpio (REW + reproducción remota en el UXX); lo esencial es: sweep suena por los JVC
   vía UXX/A50 Pro, UMIK-1 captura en el Mac, REW alinea con "timing reference acústica".
3. **Medir multipunto** (estilo Dirac): 9-13 posiciones alrededor del punto de escucha
   del escritorio (rejilla ~60×40 cm alrededor de la cabeza). Guardar los .mdat.
4. **Generar el filtro con DRC-FIR** (`apt install drc` en el UXX o brew en el Mac):
   exportar de REW las respuestas a impulso (WAV), promediarlas/ponderarlas, correr `drc`
   con preset `erb` (psicoacústico, el más parecido a Dirac) y una **curva objetivo**
   tipo Harman (tilt descendente ~−1 dB/oct suave, +2-4 dB en graves <100 Hz a gusto).
   Salida: FIR estéreo WAV (p.ej. 65536 taps, 48k, float32).
5. **CamillaDSP en el UXX**: binario Rust (release de GitHub), servicio de usuario +
   `camillagui` (web :5005) para ajustar en vivo. Pipeline: capture desde sink virtual
   PipeWire (o módulo pipewire→camilladsp vía loopback ALSA) → convolver L/R → dither →
   playback al A50 Pro. Configs versionadas en `~/.config/camilladsp/`.
   - Plan B minimalista sin CamillaDSP: `libpipewire-module-filter-chain` con
     `builtin convolver` cargando los mismos WAV (menos flexible, cero dependencias).
6. **Toggle + verificación**: `audioctl eq on/off`; A/B con temas conocidos; verificar
   headroom (sin clipping con música a 0 dBFS: pico del filtro + señal < 0 dBFS);
   REW de verificación (medir de nuevo CON corrección → la curva debe pegarse al target).
7. **Documentar**: actualizar `~/nada/office-uxx-manual.md` + memoria de Claude +
   `~/nada/audio-calidad-setup.md` (el camino DSP rompe bit-perfect por diseño, dejarlo claro).

8. **SIDE-QUEST (aprobado con entusiasmo por Albert, valor práctico: cero 😄):
   reverse-engineering de los presets EQ "secretos" del A50 Pro** (E0 Direct / E1 Tabebuia /
   E2 Bass / E3 Super Bass / E4 Rock / E5 Soft — SMSL no publica las curvas). Método: mismo
   sweep de REW con el ampli en E0 (referencia) y luego en E1…E5; restar cada medición contra
   E0 → la diferencia ES la curva del preset (la sala se cancela al restar). Entregable: gráfica
   de las 5 curvas secretas. Recordar: al terminar, devolver el ampli a **E0 Direct** (regla de
   la casa: toda la forma tonal se hace en el UXX; el EQ del ampli siempre apagado).

## Gotchas conocidos

- El A50 Pro es 16/48: la corrección trabaja en float y el truncado final a 16 bits con
  dither es transparente en la práctica. No es limitación real para room correction.
- Los JVC SP-UXJ60 son estanterías pequeñas: la corrección NO puede inventar graves que
  el altavoz no da — target curve realista (no pedir +10 dB a 40 Hz). Corregir modos de
  sala (picos) y asperezas de medios es donde se gana de verdad.
- Escritorio = campo cercano + reflexión de la mesa: medir con el mic en posición real
  de oreja. La mejora suele ser MUY audible en ese escenario.
- spotifyd está fijado por `PULSE_SINK` al sink del A50 Pro
  (`~/.config/systemd/user/spotifyd.service.d/pin-sink.conf`) — con EQ activo debe
  apuntar al sink DSP (o quitar el pin y que siga el default). Tenerlo en cuenta en el toggle.
- El plan multi-speaker (`multi-speaker-mpd-plan.md`) es ortogonal: el DSP corrige SOLO
  el camino del A50 Pro/despacho; los cast a Google speakers no pasan por aquí.
- Relación con memoria de Claude: `office-uxx-streamer.md` (setup actual),
  `audio-quality-format-handling.md` (bit-perfect medido hoy).
