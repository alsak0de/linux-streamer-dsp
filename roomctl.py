#!/usr/bin/env python3
"""roomctl - room correction orchestrator (runs on the Mac, next to REW's API).

correct: takes a REW measurement, generates correction filters for all targets
         (harman/reference/flat), builds CamillaDSP configs + profile.json and
         deploys them to the UXX.
"""
import json, base64, struct, math, subprocess, sys, time, urllib.request

REW = "http://localhost:4735"
TARGETS_DIR = "/Users/albert/nada/room-correction/targets"
UXX = "uxx"
CORRECT_RANGE = (40, 300)          # C920 mic: solo graves/medios fiables
MAX_BOOST = 3

def api(path, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(REW + path, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    try: return json.loads(raw)
    except json.JSONDecodeError: return raw

def get_curve(path):
    fr = api(path)
    b = base64.b64decode(fr["magnitude"])
    mag = struct.unpack(f">{len(b)//4}f", b)
    freqs = [fr["startFreq"] * math.exp(i * math.log(2) / fr["ppo"]) for i in range(len(mag))]
    return freqs, list(mag)

def downsample(freqs, mag, n=140, lo=20, hi=20000):
    out = []
    for i in range(n):
        f = lo * math.exp(i * math.log(hi / lo) / (n - 1))
        j = min(range(len(freqs)), key=lambda k: abs(freqs[k] - f))
        out.append([round(freqs[j], 1), round(mag[j], 2)])
    return out

def norm(points, reffreqs=(200, 2000)):
    vals = [m for f, m in points if reffreqs[0] <= f <= reffreqs[1]]
    ref = sorted(vals)[len(vals)//2] if vals else 0
    return [[f, round(m - ref, 2)] for f, m in points]

def rms_dev(points, lo, hi):
    vals = [m for f, m in points if lo <= f <= hi]
    if not vals: return None
    mean = sum(vals)/len(vals)
    return round((sum((v-mean)**2 for v in vals)/len(vals))**0.5, 2)

def correct(mid, mic_note):
    api("/application/blocking", True)
    meas = api(f"/measurements/{mid}")
    title = meas.get("title", f"id{mid}")
    print(f"== corrigiendo sobre: {title} ==")
    api(f"/measurements/{mid}/equaliser", {"manufacturer": "CamillaDSP", "model": "Filters"})
    api(f"/measurements/{mid}/target-settings", {"shape": "Full range"})
    api("/eq/match-target-settings", {
        "startFrequency": CORRECT_RANGE[0], "endFrequency": CORRECT_RANGE[1],
        "individualMaxBoostdB": MAX_BOOST, "overallMaxBoostdB": MAX_BOOST,
        "flatnessTargetdB": 1, "allowNarrowFiltersBelow200Hz": True,
        "varyQAbove200Hz": False, "allowLowShelf": False, "allowHighShelf": False})

    measured = norm(downsample(*get_curve(f"/measurements/{mid}/frequency-response?smoothing=1%2F6")))
    profile = {"created": time.strftime("%Y-%m-%d %H:%M"), "source_measurement": title,
               "mic": mic_note, "positions": 1, "range_hz": list(CORRECT_RANGE),
               "measured": measured, "targets": {}}

    for tname in ("harman", "reference", "flat"):
        print(f"-- target {tname} --")
        if tname == "flat":
            try: api("/eq/house-curve", None, method="DELETE")
            except Exception: pass
        else:
            api("/eq/house-curve", f"{TARGETS_DIR}/{'harman-room' if tname=='harman' else tname}.txt")
        api(f"/measurements/{mid}/eq/command", {"command": "Calculate target level"})
        api(f"/measurements/{mid}/eq/command", {"command": "Match target"})
        time.sleep(0.5)
        flt = [f for f in api(f"/measurements/{mid}/filters")
               if f.get("type") == "PK" and f.get("frequency")]
        # sanity: descartar cortes absurdos (>15 dB) que el mic malo pueda inducir
        flt = [f for f in flt if -15 <= f.get("gaindB", 0) <= MAX_BOOST]
        predicted = norm(downsample(*get_curve(f"/measurements/{mid}/eq/frequency-response?smoothing=1%2F6")))
        target_resp = norm(downsample(*get_curve(f"/measurements/{mid}/target-response")))
        profile["targets"][tname] = {
            "filters": [{"freq": round(f["frequency"], 1), "gain": round(f["gaindB"], 2),
                         "q": round(f["q"], 2)} for f in flt],
            "predicted": predicted, "target": target_resp,
            "accuracy_db": rms_dev(predicted, *CORRECT_RANGE),
            "accuracy_before_db": rms_dev(measured, *CORRECT_RANGE)}
        print(f"   {len(flt)} filtros | RMS {CORRECT_RANGE}: {profile['targets'][tname]['accuracy_before_db']} -> {profile['targets'][tname]['accuracy_db']} dB")

    # RT60 para decays de la tabla de modos
    try:
        api(f"/measurements/{mid}/command", {"command": "Generate RT60",
                                             "parameters": {"filterOrder": 6, "octaveFrac": 3}})
        time.sleep(0.5)
        rt = api(f"/measurements/{mid}/rt60?octaveFrac=3")
        profile["rt60"] = {k: round(v.get("Topt", 0), 3) for k, v in rt.items()
                          if isinstance(v, dict) and v.get("Topt")}
    except Exception as e:
        print("   rt60:", e)

    # modos = filtros del target harman (los picos que corrige)
    profile["modes"] = []
    for f in profile["targets"]["harman"]["filters"]:
        if f["gain"] < -1.5:
            band = min(profile.get("rt60", {}).keys(),
                       key=lambda b: abs(float(b) - f["freq"])) if profile.get("rt60") else None
            profile["modes"].append({"freq": f["freq"], "peak_db": round(-f["gain"], 1),
                                     "decay_s": profile["rt60"].get(band) if band else None})

    out = "/Users/albert/nada/room-correction/profile.json"
    json.dump(profile, open(out, "w"), indent=1)
    print(f"profile.json: {out}")
    return profile

def camilla_yaml(filters):
    peak = max([f["gain"] for f in filters] + [0])
    pre = -(peak + 1) if peak > 0 else -1.0
    lines = ["devices:", "  samplerate: 48000", "  chunksize: 1024",
             "  capture:", "    type: PipeWire", "    channels: 2",
             "    node_name: cdsp-room-capture", '    autoconnect_to: "dsp_room"',
             "  playback:", "    type: PipeWire", "    channels: 2",
             "    node_name: cdsp-room-playback", '    autoconnect_to: "dsp_loudness"',
             "filters:",
             "  room_pre:", "    type: Gain", f"    parameters: {{gain: {pre}}}"]
    names = ["room_pre"]
    for i, f in enumerate(filters):
        n = f"room_f{i}"
        names.append(n)
        lines += [f"  {n}:", "    type: Biquad",
                  f"    parameters: {{type: Peaking, freq: {f['freq']}, gain: {f['gain']}, q: {f['q']}}}"]
    lines += ["mixers: {}", "pipeline:",
              f"  - type: Filter", f"    channels: [0, 1]", f"    names: [{', '.join(names)}]"]
    return "\n".join(lines) + "\n"

def deploy(profile):
    import tempfile, os
    d = tempfile.mkdtemp()
    for t, td in profile["targets"].items():
        open(f"{d}/{t}.yml", "w").write(camilla_yaml(td["filters"]))
    subprocess.run(["ssh", UXX, "mkdir -p ~/.config/camilladsp/targets ~/.config/room-correction"], check=True)
    subprocess.run(["scp", "-q"] + [f"{d}/{t}.yml" for t in profile["targets"]] +
                   [f"{UXX}:.config/camilladsp/targets/"], check=True)
    subprocess.run(["scp", "-q", "/Users/albert/nada/room-correction/profile.json",
                    f"{UXX}:.config/room-correction/profile.json"], check=True)
    print("desplegado en uxx: targets/{harman,reference,flat}.yml + profile.json")

if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "3"
    prof = correct(mid, "C920 webcam (sin calibrar; correccion limitada a 40-300 Hz)")
    deploy(prof)
