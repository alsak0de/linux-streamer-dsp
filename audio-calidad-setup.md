# Sistema de audio — calidad de reproducción y limitaciones

> Documento de referencia. Mediciones **objetivas** (no de oído) tomadas el **2026‑07‑01**
> sobre las dos salas relevantes para calidad: **Despacho (UXX)** y **Sala 1 / HomeStation
> (aslmini → Marantz)**. Misma cuenta Spotify y misma biblioteca FLAC en ambas.

---

## 1. Resumen en una frase

- **Sala 1 (Marantz)** = donde tu **hi‑res (24/192, DSD) se disfruta ÍNTEGRO y bit‑perfect**.
- **Despacho (A50 Pro por USB)** = techo **16/48** por hardware; el **CD ya es bit‑perfect**,
  el hi‑res se **remuestrea limpio** a 16/48 (sin beneficio audible ahí).
- **Spotify = Vorbis 320 (lossy) en las dos salas** → para calidad máxima, tu biblioteca por MPD.

---

## 2. Las dos cadenas de señal

### Despacho (Room 3)
```
Biblioteca FLAC (aslmini:/Volumes/music, vía sshfs)
  → MPD local (UXX)                     [mixer_type none, sin volumen sw]
  → PipeWire                            [unidad 1.0, sin dither, rates permitidos {44100,48000}]
  → USB → SMSL A50 Pro                  [UAC1 full-speed, S16_LE, {44.1,48}, ADAPTIVE]
  → amplificador → altavoces JVC
Spotify: móvil → spotifyd "Office-UXX"  → PipeWire → A50 Pro   (Vorbis 320)
```
**Volumen**: solo el mando analógico del A50 Pro. En digital todo va a **fondo de escala (0 dBFS,
unidad)** → bit‑perfect donde el rate coincide.

### Sala 1 (Room 1) — HomeStation
```
Misma biblioteca → MPD (aslmini)        [mixer_type none, dop="no", sin resampleo]
  → HDMI (hw:0,7) → Marantz Cinema 70s  [LPCM hasta 8ch / 192 kHz / 24 bit]
  → etapa de potencia → B&W (home theater)
```

---

## 3. Capacidades reales del hardware (medidas)

### SMSL A50 Pro (USB) — `/proc/asound/card0/stream0`
```
Playback:  Format S16_LE · 2ch · Rates {44100, 48000} · 16 bits · ADAPTIVE
Capture :  Format S16_LE · 2ch · Rates {44100, 48000} · 16 bits   (ADC, sin usar)
```
→ **Techo duro 16/48 por USB.** (Su entrada **óptica** sí hace 24/192, pero no la usamos.)

### Marantz Cinema 70s (HDMI) — ELD con el AVR **encendido**
```
LPCM · 8ch · Rates {32000 44100 48000 88200 96000 176400 192000} · Bits {16, 20, 24}
(+ DTS‑HD / TrueHD hasta 192k/8ch)
```
> ⚠️ En **STANDBY** el Marantz anuncia un ELD de reserva falso: `2ch / 16 / 48`. Para medir
> capacidades reales el AVR **debe estar encendido**. Estado por MQTT: `home/marantz/power`.

---

## 4. Matriz objetiva — qué llega a cada DAC

| Formato origen | MPD decodifica | **Despacho → A50 Pro** | **Sala 1 → Marantz** |
|---|---|---|---|
| **CD FLAC 16/44.1** | `44100:16:2` | `S16 / 44100` ✅ **bit‑perfect** | `S…/44100` bit‑perfect |
| **Hi‑res 24/96** | `96000:24:2` | `S16 / 48000` (↓2:1 + 24→16) | **`S32 / 96000`** ✅ íntegro |
| **Hi‑res 24/192** | `192000:24:2` | `S16 / 48000` (↓4:1 + 24→16) | **`S32 / 192000`** ✅ íntegro |
| **DSD64 (SACD)** | `dsd64` | `S16 / 44100` | `S32 / 192000` (DSD→PCM) |
| **Spotify** | Vorbis 320 (~44.1) | `S16 / 44100` | Vorbis 320 |

Notas:
- **`S32_LE` en HDMI** = contenedor de 32 bits; dentro viajan los **24 bits reales** de origen,
  sin tocar (MPD `mixer_type none`, rate nativo, sin resampleo) → **hi‑res bit‑perfect**.
- **Bit‑perfect del CD (Despacho)**: demostrado por construcción — rate 44.1 = origen 44.1,
  ganancia **1.000**, **sin dither** (`dither.method`=none), y 16 bits caben exactos en el
  float32 interno → paso identidad. (Es el mismo criterio con que Roon/JRiver certifican bit‑perfect.)

---

## 5. Cómo se comporta el remuestreo (Despacho)

PipeWire mantiene cada contenido **en su familia de reloj**, con `allowed-rates = {44100, 48000}`:

| Familia 44.1 | → device **44100** | Familia 48 | → device **48000** |
|---|---|---|---|
| CD 44.1, DSD64 (→44.1), Spotify | sin/ratio limpio | 96k (2:1), 192k (4:1) | ratio entero |

→ **Nunca** ocurre la conversión fraccionaria fea 44.1↔48. Todo downsample es **ratio entero**
(2:1, 4:1, 64:1). Sin dither, sin atenuación. Es lo **óptimo posible** con un DAC que topa en 48k.

---

## 6. Limitaciones (y de quién es la culpa)

| Limitación | Causa | ¿Se puede mejorar? |
|---|---|---|
| **Despacho topa en 16/48** | Hardware USB del A50 Pro (UAC1) | Sí: usar su **óptica** (24/192) con puente USB→TOSLINK, u otro DAC USB async 24‑bit |
| **Hi‑res se pierde en el Despacho** | Consecuencia del punto anterior | Igual que arriba. Para *ese* cuarto, el CD ya basta |
| **DSD no es nativo** (se pasa a PCM) | `dop="no"` en MPD (ambas salas) | Sala 1: activar **DoP** si el Marantz lo acepta. Hoy DSD64→PCM 24/192, ya excelente |
| **Spotify = Vorbis 320 lossy** | Spotify **no sirve FLAC lossless** por Connect a terceros (librespot/spotifyd bloqueados aguas arriba) | No con Spotify. Para streaming lossless: **Qobuz/Tidal** |
| **ELD falso en standby** | El Marantz reporta 16/48 apagado | Medir con el AVR **encendido** |

---

## 7. La "escalera" de calidad

1. **Mejor** — tu biblioteca **hi‑res/CD por MPD en Sala 1** (Marantz, hasta 24/192 bit‑perfect).
2. **Muy buena** — la misma biblioteca en el **Despacho** (CD bit‑perfect; hi‑res a 16/48 limpio).
3. **Casual** — **Spotify (Vorbis 320)** en cualquier sala; el camino no añade pérdida, pero el
   códec es lossy. Tu FLAC gana siempre.

**Regla práctica**: hi‑res/DSD **para la Sala 1**. En el Despacho, con **FLAC 16/44.1** vas sobrado.
Spotify, para lo ambiental.

---

## 8. Cómo reproducir las mediciones (para el futuro)

```bash
# Formato que llega al DAC (mientras suena):
#   Despacho:  /proc/asound/card0/pcm0p/sub0/hw_params
#   Sala 1:    /proc/asound/card0/pcm7p/sub0/hw_params   (HDMI dev 7)
grep -E '^(rate|format|channels):' /proc/asound/card0/pcm0p/sub0/hw_params

# Formato nativo que decodifica MPD (samplerate:bits:canales):
exec 3<>/dev/tcp/localhost/6600; read -u3 _; printf 'status\nclose\n' >&3; cat <&3 | grep '^audio:'

# Volumen PipeWire (debe ser 1.00 = bit-perfect):
wpctl get-volume @DEFAULT_AUDIO_SINK@

# Capacidades del DAC USB:
cat /proc/asound/card0/stream0

# ELD del Marantz (AVR encendido) — capacidades LPCM anunciadas:
grep -iE 'monitor_name|^sad0_(rates|bits|channels)' /proc/asound/card0/eld#0.3

# Catalogar formatos de la biblioteca FLAC:
metaflac --show-sample-rate --show-bps <fichero.flac>

# Estado del Marantz (MQTT):  home/marantz/power  |  home/marantz/source
```

---

## 9. Ajustes clave que garantizan la calidad

- **UXX** `~/.config/pipewire/pipewire.conf.d/10-rates.conf`: `allowed-rates = {44100, 48000}`
  (device sigue el rate del origen; solo ratios enteros).
- **UXX** `unity-volume.service`: fuerza el sink a **1.0** en cada arranque (bit‑perfect).
- **UXX** onboard audio (`snd_hda_intel`) **deshabilitado** → único sink = A50 Pro.
- **UXX** spotifyd fijado al A50 Pro (`PULSE_SINK`) → nunca se va al sink equivocado.
- **aslmini** MPD `mixer_type "none"` + sin resampleo → hi‑res bit‑perfect al Marantz.
- **Sin dither, sin volumen software** en ninguna de las dos salas.
