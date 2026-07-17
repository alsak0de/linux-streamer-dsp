# Office UXX — Manual de uso

> Streamer del Despacho: **UXX X20** (`uxx` / `office`, $STREAMER_IP) → **SMSL A50 Pro** (USB) →
> JVC SP-UXJ60. Ver también [audio-calidad-setup.md](audio-calidad-setup.md) (límites de calidad/formato).

---

## 1. Cómo escuchar

- **Tu biblioteca (FLAC, lossless real)** → app **MPD Pilot** (o M.A.L.P.) en el iPhone,
  conectando a `$STREAMER_IP:6600`. Bit-perfect hasta 16/44.1; hi-res se remuestrea limpio a 16/48
  (techo del DAC por USB).
- **Spotify** → castea normal desde la app a **"Office-UXX"** (Spotify Connect). Calidad: Vorbis 320
  (Spotify no da lossless a dispositivos de terceros, ver doc de calidad).
- **Radio online** → en **MPD Pilot**, abre **Playlists** y carga una emisora `Radio - …`.
  Emisoras instaladas (por calidad):

  | Emisora (playlist) | Género | Calidad |
  |---|---|---|
  | `Radio - RP Main / Mellow / Rock / Global / Serenity (FLAC)` | ecléctica curada | **FLAC 16/44.1 lossless** (bit-perfect) |
  | `Radio - MotherEarth Klassik (FLAC hi-res)` | **clásica** | **FLAC 24/96 hi-res** (lossless) |
  | `Radio - MotherEarth Jazz (FLAC hi-res)` | **jazz** | **FLAC 24/96 hi-res** (lossless) |
  | `Radio - Rai Radio 3 (Clasica 320)` | clásica | MP3 320 |
  | `Radio - Adroit Jazz Underground (320)` | jazz vintage | MP3 320 |
  | `Radio - SomaFM GrooveSalad` | ambient/chill | MP3 256 |

  Notas: **hi-res FLAC de radio para clásica/jazz = solo Mother Earth** (probado; el resto del
  mundo es MP3/AAC 320). En tu A50 Pro los 24/96 bajan a 16/48 igual, pero la fuente es lossless.
  Al sintonizar a mitad de canción puede verse solo el nombre de la emisora hasta el siguiente tema.
  **Para añadir emisoras**: crear un `.m3u` con la URL del stream en
  `~/.local/share/mpd/playlists/` (en `uxx`) y `mpc update` no hace falta (las playlists se leen al
  vuelo). Evitar **TuneIn** (agregador mayormente 128 kbps). URLs FLAC de Mother Earth vía dominio
  `stream.motherearthradio.de` (el `.streamserver24.com` está muerto).
- **Solo suena una fuente a la vez**: si le das a play en una, la otra se pausa sola (el "árbitro").
- **Volumen**: SOLO con el mando físico del amplificador A50 Pro. El volumen digital está fijo a
  fondo de escala (bit-perfect) — no lo toques por software.

---

## 2. Control remoto (API HTTP, para curl / PWA / Atajos de iOS)

Base: `http://uxx.local:8080` (o `http://$STREAMER_IP:8080`). Sin autenticación (solo LAN).

| Endpoint | Qué hace |
|---|---|
| `GET /health` | ping — `{"ok":true}` |
| `GET/POST /cmd/now` | qué suena ahora mismo (texto simple) |
| `GET/POST /cmd/play` `/pause` `/toggle` `/next` `/prev` | controla la fuente activa |
| `GET/POST /cmd/stop` | **STOP general** — pausa TODO |
| `GET/POST /cmd/list` | estado de cada fuente (mpd / spotify) |
| `GET /now` | **JSON estructurado**: `{player, status, artist, title, album, length_us, position_us, art_url}` |
| `GET /cover` | bytes de la carátula embebida (si la hay); 404 si no |
| `GET/POST /cmd/dsp` | modo DSP actual: `bypass` \| `eq` \| `valve` |
| `GET/POST /cmd/dsp-bypass` `/cmd/dsp-eq` `/cmd/dsp-valve` | conmuta la capa DSP (§2b) |
| `GET/POST /cmd/dsp-valve?level=0.6&character=0.5` | válvulas con drive a medida (0–1, validado; se aplica en caliente y queda persistido) |
| `GET/POST /cmd/dsp-eq?freq=1000&gain=-3` | modo EQ + ajusta una banda (freq ∈ 31/63/125/250/500/1000/2000/4000/8000/16000; gain −12..12) |
| `POST /cmd/dsp-eq` con body JSON `{"31":2.5,"63":2,…}` | **todas las bandas en una llamada** (aplicación atómica: un solo set de PipeWire; validación completa antes de tocar nada) |
| `GET /cmd/dsp-eq-show` | ganancias actuales de las 10 bandas |

Ejemplos:
```bash
curl http://uxx.local:8080/cmd/stop
curl http://uxx.local:8080/now | python3 -m json.tool
```

> Nota: para "qué suena + carátula" en una app/dashboard, mejor usar **MQTT** (§3) — es el canal
> canónico y usa las 3 tallas de carátula de Spotify. `/now` es una comodidad REST secundaria.

## 2b. Capa DSP (rediseño final 2026-07-09: enrutado AUTOMÁTICO, sin switch)

Sinks **en serie** (`Fuente → Válvulas → EQ → A50 Pro` — orden analógico: la válvula es la etapa de ganancia, el EQ modela el resultado final con sus armónicos, y queda como última corrección antes del DAC) con **enrutado automático**: el sistema
decide solo — **si el EQ está en Off (plano) Y el Valve en Off (0/0), el audio va DIRECTO al
DAC (bypass verdadero, bit-perfect)**; en cuanto cualquier control se activa, entra la cadena.
No hay botón de modo: las cajas son la interfaz completa (EQ con preset **Off** = su
apagado; Valve con presets **Off / Subtle 0.3/0.2 / Warm 0.5/0.35 / Crunch 0.7/0.6**;
**Loudness Off/Low/Ambient**).

**Loudness (añadido 2026-07-17)** — compensación isofónica (ISO 226) para escucha a bajo
volumen: la "Dynamic EQ" de Audyssey en versión manual-honesta (el software no conoce el SPL
del mando analógico → eliges tú el nivel). Cadena: `Válvulas → EQ → Loudness → DAC`.
Niveles: **Low** (graves +4 dB, agudos +1.5, preamp −4.5) y **Ambient** (graves +8, agudos +3,
preamp −8.5) — el **preamp automático garantiza que nunca clipea** (a bajo volumen la pérdida
de SNR es irrelevante; sube un pelín el mando del ampli). CLI: `audioctl dsp loudness
{off|low|ambient|ref|show}`; API: `/cmd/dsp-loudness?level=ambient`, `/cmd/dsp-loudness-show`.
**Para comparar en serio usa `ref`** (solo CLI/API, no está en la UI): mismo preamp que
Ambient pero SIN compensación → mismo volumen global, solo cambian las curvas →
`curl ".../cmd/dsp-loudness?level=ambient"` ↔ `level=ref` alternando, sin tocar el mando.
Cualquier nivel ≠ off activa la cadena (autoroute); `dsp bypass` también lo apaga.
La línea de **signal path** dice siempre la verdad: `Source → A50 Pro · bit-perfect` o
`Source → EQ → Valve → A50 Pro`.
CLI: `audioctl dsp status` (`bypass|on`, derivado); `audioctl dsp bypass` = **apagarlo todo**
(EQ plano + valve 0/0 + directo — ojo: olvida una curva ajustada a mano; los presets están a
un tap). API: `/cmd/dsp` (estado), `/cmd/dsp-bypass` (reset total); `dsp-eq`/`dsp-valve`
ajustan y auto-enrutan.

**Interfaz web: `http://uxx.local:8080/dsp`** (también en `/`) — ahora con **dos pestañas**:
- **DSP** (funcional): botones de modo, las 10 barras del EQ con **6 presets** (Flat / Jazz /
  Classic / Rock / Funk / Pop — curvas moderadas ±3 dB; el activo resaltado) y los dos sliders
  de válvulas (drive/character).
- **Room** (✅ OPERATIVA con datos reales): corrección de sala activa — filtros generados por
  `~/nada/roomctl.py` (Mac, contra la API de REW) desde mediciones reales, desplegados a
  CamillaDSP. Switch ON/OFF, **selector de target instantáneo** (Harman/Reference/Flat —
  los 3 precalculados en la medición), gráfica measured/corrected/target real, tabla de modos
  con decay (RT60), informe TL;DR. CLI: `audioctl dsp room {on|off|status|show|target <n>}`;
  API: `/cmd/dsp-room[-on|-off|-show]`, `/cmd/dsp-room?target=X`, `GET /room/profile`.
  **Flujo para re-medir** (p.ej. con el UMIK): sesión de sweeps en REW (GUI) →
  `python3 ~/nada/roomctl.py <id_medición>` en el Mac → todo se regenera y despliega solo.
- **Caja "Player"** (global, encima de las pestañas, plegable): carátula, título/artista·álbum,
  barra de progreso (se oculta en radio), **fila de 3 fuentes al mismo nivel — `MPD | Spotify ↗ |
  Radio 📻` — con la activa resaltada en verde** (detectada en vivo: biblioteca / spotify / radio
  por URL de stream; campo `service` de `/now`). Tocar **Spotify** abre la app; tocar **Radio**
  despliega el selector de emisora (dropdown — lista en `RADIOS` de dsp.html y `audioctl radio`;
  ⚠️ sintonizar reemplaza la cola de MPD); **MPD** recuerda que la biblioteca se navega con MPD
  Pilot. Transporte (⏮ ⏯ ⏭ ⏹) y línea **signal path** con verificación bit-perfect en vivo.
  API: `/cmd/radio-<clave>`; `/cmd/radio` lista; `/now` incluye `service: mpd|spotify|radio`.
- **Todas las cajas son plegables** tocando su título (chevron ▾/▸); cada una recuerda su
  estado en el navegador (localStorage).
- **`GET /status`** (API): `{mode, chain, dac_rate, dac_format, volume, unity}` — estado del
  camino de señal para dashboards.
- **PWA**: instalable en el iPhone — abrir en Safari → Compartir → "Añadir a pantalla de inicio"
  (manifest + icono servidos por audio-http; se abre a pantalla completa sin barra de Safari).
Todo en caliente y persistente. Tocar un slider activa su modo (EQ o Valve) automáticamente.
Funciona en Mac y iPhone; integrable en la PWA como iframe o enlace.

| Modo | Qué hace | Bit-perfect |
|---|---|---|
| **bypass** (por defecto) | fuentes → SMSL directo | ✅ sí |
| **eq** | **EQ gráfico 10 bandas** por octava (31.5–16k Hz, Q 1.4), ganancias −12..+12 dB — **de fábrica plano** (transparente). Ajustable **en caliente** por banda: `/cmd/dsp-eq?freq=1000&gain=-3` (o `audioctl dsp eq 1000 -3`); estado con `/cmd/dsp-eq-show`; persiste entre reinicios | ❌ (procesa en float) |
| **valve** | saturación de válvulas (plugin LADSPA "Valve saturation" de swh-plugins): armónicos pares/H2, drive 0.35, character 0.5 | ❌ (es el objetivo 😄) |

- Implementación: sinks virtuales de PipeWire **filter-chain** (`~/.config/pipewire/pipewire.conf.d/30-dsp-eq.conf`
  y `31-dsp-valve.conf`) → salida al sink del A50 Pro. Conmutar modo = cambiar el default sink.
- **Tunear**: editar los `.conf` (Gain en dB por banda del EQ; "Distortion level/character" 0–1 del
  valve) y `systemctl --user restart pipewire wireplumber pipewire-pulse && systemctl --user restart mpd mpDris2`.
- El modo es **pegajoso entre reinicios** (WirePlumber recuerda el default). `unity-volume` fuerza
  1.0 en los tres sinks en cada arranque (nunca hay volumen software escondido).
- spotifyd ya no está clavado al SMSL: sigue el default → también pasa por el DSP activo.

---

## 3. Now-playing por MQTT (para la PWA / domótica)

- **Broker**: `aslmini:1883` (usuario `$STREAMER_USER` / `<MQTT_PASSWORD>`)
- **Topic**: `home/office-music/now-playing` (retained, se actualiza en cada cambio de canción)
- **Esquema** (igual que el resto de la casa — Sala 1 en `home/station/now-playing`):
```json
{
  "title": "...", "artist": "...", "album": "...", "year": 2007,
  "type": "music", "source": "mpd|spotify", "service": "mpd|spotify",
  "confidence": 100, "via": "office",
  "cover_large": "...", "cover_medium": "...", "cover_small": "...",
  "spotify_id": "...", "spotify_url": "...", "preview_url": null,
  "timestamp": 1234567890
}
```
Comprobar en vivo:
```bash
ssh aslmini "mosquitto_sub -h localhost -u $MQTT_USER -P <MQTT_PASSWORD> -t home/office-music/now-playing -C 1"
```

---

## 4. Servicios (systemd de usuario en `uxx`)

Todos corren como el usuario `$STREAMER_USER` (`systemctl --user ...`), con `loginctl enable-linger`
para que arranquen sin necesidad de sesión abierta.

| Servicio | Qué es |
|---|---|
| `pipewire` / `wireplumber` | backbone de audio |
| `mpd` | reproductor de la biblioteca (local, vía sshfs) |
| `sshfs-music` | monta `aslmini:/Volumes/music` → `/mnt/music` (solo lectura) |
| `spotifyd` | target de Spotify Connect "Office-UXX" |
| `mpDris2` | hace que MPD hable MPRIS (para que `playerctl` lo controle) |
| `audio-arbiter` | "una fuente a la vez": pausa las demás cuando una empieza a sonar |
| `audioctl` (no es servicio, es el comando) | `~/.local/bin/audioctl {now\|play\|pause\|toggle\|next\|prev\|stop\|list}` |
| `audio-http` | expone la API HTTP `:8080` (§2) |
| `office-nowplaying` | publica el now-playing en MQTT (§3) |
| `unity-volume` | fuerza el volumen a unidad (bit-perfect) en cada arranque |

Comandos útiles:
```bash
ssh uxx systemctl --user status <servicio>
ssh uxx systemctl --user restart <servicio>
ssh uxx journalctl --user -u <servicio> -n 30 --no-pager
```

---

## 5. Contenedores (Podman)

Para lanzar algo puntual (p. ej. `blaiseio/acelink` para AceStream):
```bash
podman run --rm -d -p <puerto>:<puerto> --name <nombre> docker.io/<imagen>
podman ps                       # ver qué corre
podman stats --no-stream <nombre>   # CPU/RAM/red que consume
podman stop <nombre>            # parar (con --rm se autodestruye)
```
No hace falta `--platform=linux/amd64` (el UXX ya es x86_64 nativo). El N3350 tiene **2 núcleos**;
`podman stats` reporta CPU normalizado a 100%=1 core (puede llegar a 200% con los 2 saturados).

---

## 6. Averías conocidas y su arreglo

- **Tras un apagón/reinicio, Spotify se conecta pero no suena** → causa: el UXX tiene un audio
  integrado (Intel HDA) sin nada enchufado, y en arranque en frío el sink por defecto puede caer
  ahí antes de que el USB enumere. Ya está **blindado**: el audio integrado está deshabilitado por
  blacklist del módulo, y spotifyd está clavado al sink del A50 Pro. Si volviera a pasar:
  `ssh uxx wpctl status` (confirmar que el sink `SMSL usb audio` es el `*` por defecto).
- **Suena flojo / no es bit-perfect tras reiniciar** → el servicio `unity-volume` debería arreglarlo
  solo en cada arranque. Si no: `ssh uxx wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.0`.
- **MPD no suena tras un reinicio** → normal: MPD no auto-arranca la reproducción, queda en pausa.
  Dale a play desde MPD Pilot o `curl .../cmd/play`.
- **El now-playing MQTT se queda "pegado" en la canción anterior** → ya solucionado (el publicador
  ahora dispara con cada cambio de pista, no solo con cambios de estado play/pausa).

---

## 7. Referencia rápida de red

| Host | Uso |
|---|---|
| `uxx` / `office` ($STREAMER_IP) | el streamer del Despacho |
| `aslmini` ($MEDIA_SERVER_IP) | biblioteca MPD origen + broker MQTT + now-playing Sala 1 |
| `jetson` | domótica "waldo" — dueño del OAuth/Web API de Spotify (misma cuenta) |
