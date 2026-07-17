# Plan: instalar myMPD (web UI para el MPD del despacho)

> **Estado: ⏪ DESHECHO (2026-07-05, mismo día).** Se instaló, funcionó, y Albert decidió
> revertirlo: prefiere controlar MPD desde el móvil (MPD Pilot) y no necesita la web UI.
> Rollback completo ejecutado: paquete + repo APT + clave + workdir + unit de usuario +
> línea de socket en mpd.conf eliminados; stack verificado sano. **NO reinstalar salvo
> petición explícita de Albert.** Se deja el resto del doc como referencia por si algún
> día se quiere de nuevo (la instalación funcionó; ver notas de desviaciones abajo).

> **Estado previo: ✅ HECHO (2026-07-05).** myMPD 25.2.2 en `http://uxx.local:8081`. Desviaciones vs
> este plan: (1) no había .deb en GitHub → se usó el repo APT oficial OBS firmado
> (`home:/jcorporation/xUbuntu_24.04`, huella de clave verificada). (2) myMPD solo autodetecta
> el music_directory por **socket Unix de MPD** → se añadió `bind_to_address ".../mpd/socket"` a
> mpd.conf (además del TCP) y se configuró la conexión por la **API JSON-RPC**
> (`MYMPD_API_CONNECTION_SAVE`), no por los ficheros `config/` (que solo se leen en el primer init).
> (3) reboot-test NO forzado (para no interrumpir escucha); el servicio queda `enable`+linger igual
> que el resto, que ya se ha probado que sobreviven a reinicios.

> **Estado original: PENDIENTE.** Objetivo: web UI bonita (estilo moOde) sobre el MPD existente del UXX.
> Este plan es AUTOCONTENIDO y prescriptivo para que cualquier sesión/LLM lo ejecute sin
> contexto adicional. NO improvisar fuera de lo escrito; si algo falla, parar y preguntar.

## Contexto mínimo (no re-derivar)

- Host: `uxx` (192.168.86.6), Ubuntu Server 24.04 (noble) amd64, usuario `albert`
  (sudo NOPASSWD). Acceso: `ssh uxx` desde el Mac de Albert.
- MPD ya corre como **servicio de usuario** de albert (`systemctl --user`), puerto **6600**
  (bind 0.0.0.0), música en `/mnt/music` (sshfs **solo lectura montado por albert** —
  ⚠️ sin `allow_other`: OTROS usuarios NO pueden leer ese punto de montaje).
- Puertos ocupados en uxx: 6600 (MPD), 8080 (audio-http API), 6878 (acelink si corre),
  5900s no. **Puerto elegido para myMPD: 8081**.
- myMPD es SOLO un cliente web de MPD (no reproduce audio él mismo) → no toca PipeWire,
  ni el árbitro, ni spotifyd, ni el publicador MQTT. Riesgo bajo.
- **NO tocar**: mpd.service, spotifyd, audio-arbiter, audio-http, office-nowplaying,
  unity-volume, sshfs-music (todos servicios de usuario de albert).

## Decisión de diseño (ya tomada, no re-debatir)

Correr myMPD como **servicio de USUARIO de albert** (no el servicio de sistema del paquete):
1) coherente con el resto del stack (todo user-level), 2) como albert puede leer
`/mnt/music` (portadas locales), el usuario de sistema `mympd` NO podría (fuse sin
allow_other), 3) puerto 8081 >1024 no necesita root.

## Pasos

### 1. Instalar el paquete
```bash
ssh uxx
# localizar el .deb de la última release para Ubuntu noble amd64:
curl -s https://api.github.com/repos/jcorporation/myMPD/releases/latest \
  | grep -oE '"browser_download_url": *"[^"]+"' | grep -i amd64 | grep -iE 'noble|ubuntu' 
# (si hay varios, elegir el de ubuntu-noble amd64; si no hay ninguno con "noble",
#  usar el genérico amd64 .deb si existe)
wget -O /tmp/mympd.deb "<URL elegida>"
sudo apt install -y /tmp/mympd.deb
mympd -v   # debe imprimir versión
```
Si NO existe .deb (improbable): parar y reportar a Albert (no compilar de fuentes sin preguntar).

### 2. Desactivar el servicio de sistema del paquete (usaremos unit de usuario)
```bash
sudo systemctl disable --now mympd.service 2>/dev/null || true
```

### 3. Crear el servicio de usuario
Fichero `~/.config/systemd/user/mympd.service` (usuario albert en uxx):
```ini
[Unit]
Description=myMPD web UI (user instance)
After=mpd.service network-online.target

[Service]
Type=simple
Environment=MPD_HOST=127.0.0.1
Environment=MPD_PORT=6600
ExecStart=/usr/bin/mympd --workdir %h/.local/share/mympd --cachedir %h/.cache/mympd
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

### 4. Configurar puerto 8081 y sin SSL (ANTES del primer arranque)
myMPD lee la config de ficheros sueltos en `{workdir}/config/`:
```bash
mkdir -p ~/.local/share/mympd/config
echo 8081  > ~/.local/share/mympd/config/http_port
echo false > ~/.local/share/mympd/config/ssl
```

### 5. Arrancar y habilitar
```bash
systemctl --user daemon-reload
systemctl --user enable --now mympd.service
sleep 3
systemctl --user is-active mympd.service    # → active
ss -ltn | grep 8081                          # → LISTEN
journalctl --user -u mympd -n 20 --no-pager  # sin errores; debe decir que conectó a MPD
```
⚠️ Recordatorio para sesiones SSH no interactivas: exportar antes
`XDG_RUNTIME_DIR=/run/user/$(id -u)` y
`DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus`.

### 6. Verificación funcional (checklist)
- [ ] `curl -s -o /dev/null -w '%{http_code}' http://localhost:8081` en uxx → 200
- [ ] Desde el Mac: abrir `http://uxx.local:8081` → carga la UI
- [ ] La UI muestra la biblioteca (DB del MPD existente — Amy Winehouse, Miles Davis,
      Herbie Hancock, Dire Straits, Michael Jackson, Supertramp, Stan Getz…)
- [ ] Las playlists `Radio - *` aparecen (Radio Paradise FLAC, MotherEarth, etc.)
- [ ] Play/pausa desde la UI funciona y suena por el A50 Pro
- [ ] Si a la vez se lanza Spotify (castear a "Office-UXX"), el árbitro pausa MPD (nada roto)
- [ ] `curl http://uxx.local:8080/cmd/now` sigue funcionando (API intacta en 8080)
- [ ] El topic MQTT `home/office-music/now-playing` se actualiza al reproducir desde myMPD
- [ ] Reboot de uxx (`sudo reboot`, esperar ~90 s) → myMPD vuelve solo en 8081

### 7. Documentar al terminar (OBLIGATORIO)
- `~/nada/office-uxx-manual.md` (en el Mac de Albert): añadir en "Cómo escuchar":
  web UI en `http://uxx.local:8081` (myMPD) — biblioteca, radios y cola desde cualquier
  navegador (Mac/iPhone). Y añadir `mympd` a la tabla de servicios (§4).
- Memoria de Claude: en `office-uxx-streamer.md` añadir una línea: myMPD instalado como
  user service, puerto 8081, workdir `~/.local/share/mympd`, cliente-only (riesgo cero
  para el audio path). Marcar este plan como HECHO (editar la cabecera de este fichero).

## Rollback (si algo va mal)
```bash
systemctl --user disable --now mympd.service
rm ~/.config/systemd/user/mympd.service; systemctl --user daemon-reload
sudo apt remove -y mympd
rm -rf ~/.local/share/mympd ~/.cache/mympd
```
El stack de audio no se ve afectado en ningún caso (myMPD es solo un cliente).

## Notas / gotchas conocidos
- Portadas: la biblioteca de Albert casi no tiene covers embebidos (rips SACD/DSD), así
  que myMPD mostrará muchas carátulas vacías — ES ESPERADO, no es un fallo. (Las radios
  y lo que tenga tags sí mostrarán arte. No intentar "arreglarlo" instalando nada.)
- No abrir el puerto 80 ni usar SSL: LAN interna, decisión de Albert (igual que audio-http).
- myMPD tiene favoritos de webradio propios (WebradioDB); opcional: añadir ahí las
  emisoras del despacho (Radio Paradise FLAC etc.) para acceso con un clic. Solo si
  Albert lo pide.
- Si la UI pidiera un "pin" de configuración inicial: no configurar pin (LAN de confianza).
