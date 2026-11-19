import json
import urllib.request
import urllib.error
import datetime

# ---- Settings you can change ----
HOST = "http://localhost:11434"   # Ollama's local API
PROMPT = "Explain what an internally displaced person is, in two sentences."
POWER_LOW_W = 15        # assumed laptop power, low end (NOT measured)
POWER_HIGH_W = 45       # assumed laptop power, high end (NOT measured)
GRID_G_PER_KWH = 169    # Austria 2025, Electricity Maps
MAX_TOKENS = 300        # cap so "thinking" ends in about a minute


def get_json(url):
    # Simple GET that returns parsed JSON
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def post_json(url, body):
    # Simple POST that returns parsed JSON
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.loads(r.read())


def list_models():
    # Ask Ollama which models are installed on this computer
    data = get_json(HOST + "/api/tags")
    names = [m["name"] for m in data.get("models", [])]
    local = [n for n in names if not n.endswith(":cloud")]  # skip cloud models
    return names, local


def pick_model(local):
    # Prefer a known small model, otherwise take the first local one
    for preferred in ("qwen3.5:4b", "qwen3:4b"):
        if preferred in local:
            return preferred
    return local[0] if local else None


def run_once(model, think):
    # Send one question and return Ollama's statistics
    body = {
        "model": model,
        "prompt": PROMPT,
        "stream": False,
        "think": think,                       # True = reasoning, False = off
        "options": {"num_predict": MAX_TOKENS},
    }
    return post_json(HOST + "/api/generate", body)


def summarize(d):
    # Turn raw stats into energy and CO2
    total_s = d["total_duration"] / 1e9       # nanoseconds -> seconds
    tokens = d.get("eval_count", 0)
    wh_low = POWER_LOW_W * total_s / 3600     # energy = power x time
    wh_high = POWER_HIGH_W * total_s / 3600
    g_low = wh_low / 1000 * GRID_G_PER_KWH    # CO2 = energy(kWh) x grid
    g_high = wh_high / 1000 * GRID_G_PER_KWH
    return {
        "time_s": round(total_s, 1),
        "tokens": tokens,
        "wh_low": round(wh_low, 3), "wh_high": round(wh_high, 3),
        "g_low": round(g_low, 4), "g_high": round(g_high, 4),
        "capped": d.get("done_reason") == "length",
    }


def main():
    # Step 1: find installed models
    try:
        all_names, local = list_models()
    except urllib.error.URLError:
        print("Could not reach Ollama. Is it running? Try 'ollama serve' in another terminal.")
        return

    print("Installed models:", ", ".join(all_names) if all_names else "(none)")
    if not local:
        print("No local model found. Run for example: ollama pull qwen3.5:4b")
        return

    model = pick_model(local)
    print("Using model:", model)

    # Step 2: warm up (first call loads the model, do not measure it)
    print("Warming up...")
    run_once(model, False)

    # Step 3: measure both modes
    results = {}
    for label, think in [("no_thinking", False), ("thinking", True)]:
        print(f"\nRunning: {label} ... (please wait)")
        s = summarize(run_once(model, think))
        results[label] = s
        print(f"  time:   {s['time_s']} s")
        print(f"  tokens: {s['tokens']}" + ("  (stopped at token cap)" if s["capped"] else ""))
        print(f"  energy: {s['wh_low']} to {s['wh_high']} Wh (assuming {POWER_LOW_W}-{POWER_HIGH_W} W)")
        print(f"  CO2:    {s['g_low']} to {s['g_high']} g (at {GRID_G_PER_KWH} g/kWh)")

    # Step 4: save everything to a file
    out = {
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "assumptions": {"power_low_W": POWER_LOW_W, "power_high_W": POWER_HIGH_W, "grid_g_per_kWh": GRID_G_PER_KWH},
        "results": results,
    }
    with open("measurements.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nSaved to measurements.json")


main()