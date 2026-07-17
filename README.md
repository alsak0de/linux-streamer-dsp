# linux-streamer-dsp

A DIY **headless, bit-perfect Linux streamer** with a fully switchable DSP stack and
**measurement-based room correction**, built on a €55 fanless x86 mini-PC feeding a USB
DAC/amp — controlled from a self-hosted web app (PWA) on the phone.

> Discussion thread: AVSForum (see my post). This repo doubles as the project's working
> notes and backup — docs are a mix of English (interfaces) and Spanish (build notes).

## What it does

- **Bit-perfect playback** (PipeWire backbone, unity gain, no software volume, no dither,
  integer-ratio-only resampling) from: **MPD** (FLAC library over the LAN), **Spotify
  Connect** (spotifyd/librespot), and **FLAC internet radio** (Radio Paradise, Mother
  Earth 24/96).
- **DSP chain in analog order** — `tube saturation → 10-band EQ → equal-loudness
  compensation (ISO 226, my manual take on Audyssey Dynamic EQ)` — with **automatic
  routing**: everything off ⇒ audio physically bypasses the chain (true bit-perfect).
- **Room correction**: REW's REST API orchestrated by [`roomctl.py`](roomctl.py) —
  sweeps measured offline (the streamer plays the stimulus through the real chain),
  auto-EQ against 3 target curves at once (Harman / Reference / Flat), filters deployed
  natively to a **CamillaDSP** stage; instant target switching from the web app.
- **Web app / PWA**: player card (sources, cover art, transport, live signal-path with
  bit-perfect indicator), DSP controls, room-correction dashboard (measured/corrected/
  target graph, detected room modes with decay, TL;DR report).
- **Home integration**: small HTTP API (allowlisted actions) + MQTT now-playing events.

## Repo map

| File | What |
|---|---|
| `office-uxx-manual.md` | User manual of the streamer (services, API, UI) — Spanish |
| `audio-calidad-setup.md` | Measured quality limits per source/DAC — Spanish |
| `room-correction-plan.md` | Full room-correction design, REW API findings, session logs |
| `roomctl.py` | Room-correction orchestrator (runs next to REW, deploys to streamer) |
| `rew-pipeline-test.py` | REW API pipeline validation with a synthetic room |
| `rew-openapi-0.9.5.json` | REW REST API spec dump (378 endpoints) |
| `room-correction/` | Target curves + measurement profile |
| `multi-speaker-mpd-plan.md`, `mympd-plan.md` | Future/parked plans |
| `*.mdat`, `sweep.wav` | REW measurements + stimulus file |

## Status

Fully operational with an uncalibrated mic (correction limited to 40–300 Hz);
a UMIK-1 is on the way for full-range correction. Configuration files for the streamer
itself (PipeWire filter-chains, CamillaDSP, systemd units) will be added next.

Secrets (MQTT password, etc.) are placeholder-scrubbed — adapt to your own environment.
