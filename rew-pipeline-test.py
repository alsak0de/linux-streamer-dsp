#!/usr/bin/env python3
"""Fase 0 end-to-end: pipeline de room correction con sala SINTETICA via REW API."""
import json, base64, math, urllib.request, sys, time

REW = "http://localhost:4735"

def api(path, body=None, method=None):
    url = REW + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode()
    try: return json.loads(raw)
    except json.JSONDecodeError: return raw

print("== 0) modo blocking (comandos síncronos) ==")
print(api("/application/blocking", True))

print("== 1) sintetizar sala: impulso + modos 43/86/176 Hz ==")
FS = 48000; N = 65536
def synth(seed):
    h = [0.0]*N
    h[64] = 1.0                                   # impulso directo
    h[int(0.011*FS)+64] = 0.35                    # una reflexión temprana
    modes = [(43.0, 0.45, 0.030+0.006*seed),      # (freq, tau_s, amplitud)
             (86.0, 0.28, 0.018+0.004*seed),
             (176.0, 0.16, 0.010)]
    for f, tau, A in modes:
        w = 2*math.pi*f/FS
        for n in range(N):
            h[n] += A * math.exp(-n/(tau*FS)) * math.sin(w*n)
    return h

import struct
def b64(h):  # float32 big-endian, como documenta la API
    return base64.b64encode(struct.pack(f">{len(h)}f", *h)).decode()

for i in (1, 2):
    r = api("/import/impulse-response-data",
            {"identifier": f"Synthetic pos {i}", "startTime": 0.0,
             "sampleRate": FS, "applyCal": False, "data": b64(synth(i))})
    print(f"  import pos {i}:", r)
    time.sleep(1)

def mlist():
    d = api("/measurements")
    return [d[k] for k in sorted(d, key=int)] if isinstance(d, dict) else d

print("== 2) mediciones presentes ==")
ms = mlist()
for m in ms:
    print("  ", m.get("title"), m.get("uuid")[:8], f"{m.get('startFreq','?')}-{m.get('endFreq','?')}Hz")
uuids = [m["uuid"] for m in ms if str(m.get("title","")).startswith("Synthetic")]
assert len(uuids) >= 2, "no se importaron las 2 sintéticas"

print("== 3) promedio vectorial (multipunto) ==")
r = api("/measurements/process-measurements",
        {"processName": "Vector average", "measurementUUIDs": uuids[:2]})
print("  ", r)
time.sleep(1)
ms = mlist()
avg = ms[-1]
print("   promedio =", avg.get("title"), avg["uuid"][:8])
AID = avg["uuid"]

print("== 4) equaliser = CamillaDSP + target + match settings ==")
print("  equaliser:", api(f"/measurements/{AID}/equaliser",
      {"manufacturer": "CamillaDSP", "model": "Filters"}))
print("  target-settings:", api(f"/measurements/{AID}/target-settings", {"shape": "Full range"}))
print("  target level:", api(f"/measurements/{AID}/eq/command", {"command": "Calculate target level"}))
print("  match-settings:", api("/eq/match-target-settings",
      {"startFrequency": 20, "endFrequency": 300, "individualMaxBoostdB": 3,
       "overallMaxBoostdB": 3, "flatnessTargetdB": 1,
       "allowNarrowFiltersBelow200Hz": True, "varyQAbove200Hz": False,
       "allowLowShelf": False, "allowHighShelf": False}))

print("== 5) MATCH TARGET (auto-EQ) ==")
print("  ", api(f"/measurements/{AID}/eq/command", {"command": "Match target"}))
time.sleep(1)

print("== 6) filtros generados (formato CamillaDSP) ==")
flt = api(f"/measurements/{AID}/filters")
for f in flt:
    if f.get("type") not in (None, "None"):
        print(f"   {f.get('type','?'):6} fc={f.get('frequency','?'):>7} Hz  gain={f.get('gaindB','?'):>6} dB  Q={f.get('q','?')}")

print("== 7) prediccion (medicion corregida) ==")
print("  ", api(f"/measurements/{AID}/eq/command", {"command": "Generate predicted measurement"}))
time.sleep(1)
ms = mlist()
print("   nueva:", ms[-1].get("title"))

print("== 8) RT60 del promedio ==")
r = api(f"/measurements/{AID}/command", {"command": "Generate RT60"})
print("  gen:", r); time.sleep(1)
try:
    rt = api(f"/measurements/{AID}/rt60")
    s = json.dumps(rt)
    print("  rt60 keys:", list(rt.keys())[:8] if isinstance(rt, dict) else type(rt), len(s), "bytes")
except Exception as e:
    print("  rt60 GET:", e)

print("\n✅ PIPELINE COMPLETO EJECUTADO")
