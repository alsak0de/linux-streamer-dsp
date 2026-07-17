# Plan: servidores MPD "virtuales" por altavoz (cast a Google Home/Nest/CCA)

> **Estado: PENDIENTE de implementar** (diseño acordado con Albert 2026-07-03).
> Objetivo de este doc: que una sesión futura de Claude pueda montarlo sin releer la conversación.
> Máquina: `uxx` (192.168.86.6, Ubuntu 24.04, usuario albert, sudo NOPASSWD, alias ssh `uxx`).

## Idea (decidida por Albert — no re-debatir)

En MPD Pilot ya se cambia de servidor MPD como quien cambia de sala. Pues eso mismo para
elegir altavoz: **una instancia MPD por altavoz de cast**. Cada instancia = su propia cola +
estado, ligada 1:1 a un altavoz Google (Home Mini / Nest / Chromecast Audio). Elegir altavoz
= elegir servidor en MPD Pilot. NO es multiroom sincronizado (filosofía: salas independientes).

| Servidor (zeroconf) | Puerto MPD | Salida audio | Destino |
|---|---|---|---|
| Office (EXISTENTE, no tocar) | 6600 | pipewire → A50 Pro | bit-perfect local |
| `<sala 1, p.ej. Cocina>` | 6601 | httpd :8001 (flac o lame 320) | Google Nest/Home vía catt |
| `<sala 2…>` | 6602 | httpd :8002 | otro altavoz |
| Porche (futuro, CCA) | 6603 | httpd :8003 | Chromecast Audio |
| Móvil/auriculares (decidido 2026-07-05) | 6604 | httpd :8004 | **MPD Pilot "Local Playback"** en el iPhone — SIN watcher ni catt: la app tira del stream ella sola (config en la app: servidor 6604 + stream URL :8004) |

**Decisión de Albert (2026-07-05):** NO añadir salida httpd al MPD principal del Office
(acoplaría la cola del hifi al móvil vía fan-out). La escucha en el móvil "de verdad" será
una **instancia virtual propia** (fila de arriba): cola desacoplada de los sistemas hifi.
Mientras tanto, para escuchar en el iPhone ya le vale el stream httpd existente de
**aslmini :8001** (servidor aslmini en MPD Pilot).

**PREGUNTAR a Albert al empezar: qué altavoces Google tiene, nombre cast de cada uno
(`catt scan`), y qué nombre quiere para cada servidor.**

### ⏸️ DECISIÓN ABIERTA (aparcada 2026-07-05): modelo A vs B — NO decidir por él, preguntar

Dos arquitecturas sobre la mesa, ambas válidas; Albert las considera sin decidir:
- **A) Una instancia MPD por altavoz/sala** (lo que describe la tabla de arriba). Elegir sala =
  elegir servidor en MPD Pilot. Permite Google distintos sonando cosas distintas a la vez.
- **B) Un "caster" genérico reapuntable** (1 instancia, catt apunta al Google que elijas en el
  momento). Menos instancias, pero elegir sala vive FUERA de MPD Pilot (PWA / `audioctl cast <x>`),
  y solo un Google a la vez.
- Deciding question que se le planteó: *¿querrá 2 Google sonando distinto a la vez?* Si no → B encaja
  con su filosofía "una sala a la vez"; pero Albert ve que A (instancia por sala) también tiene
  sentido (control todo dentro de MPD Pilot, coste ~20MB/instancia irrelevante). **Sin resolver.**

### Alexa — FUERA de scope (decidido 2026-07-05)
No hablan Google Cast → catt no los maneja. Spotify en Echo ya lo cubre waldo (Connect Web API);
la biblioteca MPD en un Echo solo sería por Bluetooth (SBC lossy, feo) → NO se hace. Los Echo no
son endpoints de biblioteca; para biblioteca en una sala, usar Google/Nest/Chromecast Audio.

## Estado actual del UXX (contexto mínimo)

- MPD principal: servicio de usuario `mpd.service`, config `~/.config/mpd/mpd.conf`,
  puerto 6600, biblioteca **ro** en `/mnt/music` (sshfs desde aslmini, servicio
  `sshfs-music.service`), db/estado en `~/.local/share/mpd/`, playlists (radios) en
  `~/.local/share/mpd/playlists/`, salida pipewire `mixer_type "none"` (bit-perfect;
  volumen SOLO en el ampli).
- Servicios de usuario relacionados: `mpDris2` (MPRIS del MPD principal), `audio-arbiter`
  (una fuente a la vez SOLO para el A50 Pro: mpd vs spotifyd — NO debe arbitrar las
  instancias nuevas), `audio-http` (API :8080), `office-nowplaying` (publica MQTT
  `home/office-music/now-playing`, broker aslmini:1883, creds albert/<MQTT_PASSWORD>, esquema §3.1).
- Manual de uso: `~/nada/office-uxx-manual.md` (actualizar al terminar).

## Implementación (pasos)

1. **catt**: `sudo apt install catt` o `pipx install catt`. Verificar descubrimiento:
   `catt scan` (mDNS en la LAN). Anotar nombres exactos de los altavoces.

2. **Template de instancia** `~/.config/systemd/user/mpd@.service` + config por sala
   `~/.config/mpd/mpd-<sala>.conf` con:
   - `port 660N`, `bind_to_address "0.0.0.0"`
   - **DB por proxy** (clave: NO re-escanear la biblioteca):
     ```
     database { plugin "proxy"  host "localhost"  port "6600" }
     ```
   - `music_directory "/mnt/music"` (mismo ro)
   - `playlist_directory` → symlink o la misma ruta que el principal (compartir radios)
   - state/sticker propios: `~/.local/share/mpd-<sala>/`
   - salida:
     ```
     audio_output {
         type "httpd"  name "<sala> stream"  port "800N"
         encoder "flac"            # probar FLAC en Nest; fallback: lame bitrate 320
         format "44100:16:2"  always_on "yes"  tags "yes"
     }
     ```
   - `mixer_type "software"` en estas instancias (la rueda de volumen de MPD Pilot
     funciona; aquí no aplica el bit-perfect — el Office se queda como está)
   - `zeroconf_enabled "yes"`, `zeroconf_name "<sala>"` → MPD Pilot los autodescubre.

3. **Watcher-cast por sala** (el pegamento instancia→altavoz; patrón = audio-arbiter):
   script único parametrizado `~/.local/bin/cast-watcher <puerto_mpd> <nombre_cast> <url_stream>`
   + template `cast-watcher@<sala>.service`. Lógica: bucle `mpc -p 660N idle player`;
   en estado *play* → `catt -d "<nombre_cast>" cast_site <url>`… (usar `catt cast <url>`);
   en *pause/stop* → `catt -d "<nombre_cast>" stop`. Debounce de ~2 s. Nota: el
   Chromecast tarda 2-4 s en engancharse (buffering normal).

4. **Now-playing MQTT por sala**: extender `~/.local/bin/office-nowplaying` (o clonar
   parametrizado) para sondear cada instancia (puerto) y publicar en
   `home/<sala>-music/now-playing` con el MISMO esquema §3.1 (retained, QoS1). El
   publicador actual usa MPRIS/playerctl; para instancias extra es más simple ir
   directo al protocolo MPD (`currentsong`/`idle`) que multiplicar mpDris2.

5. **NO tocar**: `mpd.service` principal, `audio-arbiter` (solo arbitra A50 Pro),
   `unity-volume`, spotifyd, blacklist de audio onboard.

6. **Verificación**: (a) MPD Pilot ve los servidores nuevos por zeroconf; (b) play en
   instancia Cocina → suena en el Nest (~3 s); (c) pause → el Nest calla; (d) cola de
   Office y Cocina independientes y simultáneas; (e) topic MQTT nuevo publica; (f) radios
   (playlists `Radio - *`) cargables desde la instancia nueva; (g) reboot → todo vuelve.

7. **Actualizar al terminar**: `~/nada/office-uxx-manual.md` (sección "Cómo escuchar"),
   memoria de Claude (`office-uxx-streamer.md`), y este fichero (marcar HECHO).

## Gotchas conocidos

- catt es la única dependencia nueva; usa mDNS (la red Google Wifi de Albert lo pasa bien).
- FLAC httpd: los Nest lo aceptan según specs de Google Cast; si un Home Mini viejo
  tose, cambiar encoder a `lame` 320 en su config y listo.
- `always_on yes` en httpd evita que el stream se caiga entre pistas (gapless razonable).
- El proxy-db requiere el MPD principal levantado (dependencia `After=mpd.service` en el
  template).
- RAM por instancia: ~15-25 MB. Irrelevante (6 GB).
- Alexa/Echo: DESCARTADO para biblioteca MPD (sin API oficial, hacks frágiles). Spotify
  en Alexa ya lo cubre waldo/jetson por Spotify Connect Web API (misma cuenta).
- Radio en altavoz: el watcher castea el stream httpd de la instancia (uniforme). Castear
  la URL de la emisora directo al altavoz sería posible pero rompe la uniformidad
  (cola/control/now-playing) — no hacerlo salvo que Albert lo pida.
