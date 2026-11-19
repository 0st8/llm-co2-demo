# llm-co2-demo

Measuring the energy and CO₂ cost of **one AI chat answer** on a laptop, and
comparing it with published estimates for cloud chatbots.

Part of the course *VU Tools in Data Science* (Green AI topic). Code and notes
were written with help from AI (Claude); all measurements were run by me.

## The question

How much energy and CO₂ does a single answer from a language model cost? I
measure a small model running locally with [Ollama](https://ollama.com), and
compare it with published numbers for cloud chatbots.

## The two formulas

```
Energy (Wh) = Power (W) × Time (hours)
CO₂ (g)     = Energy (kWh) × Grid intensity (g CO₂ per kWh)
```

- Grid intensity: Austria 2025 ≈ **169 g CO₂/kWh** (Electricity Maps).
- This counts **inference** (answering) only, not the one-time cost of
  **training** a model.

## What `measure.py` does

1. Asks Ollama which models are installed (`/api/tags`) and picks a local one
   (skips cloud models).
2. Warms up the model — the first call loads it into memory, which is not part
   of answering, so it is not measured.
3. Runs the same question twice: **thinking off** and **thinking on** (capped at
   300 tokens so it does not run for minutes).
4. Reads Ollama's time and token count, and computes energy and CO₂.
5. Saves everything to `measurements.json`.

## Run it

Needs Python and Ollama with a local model, for example:

```
ollama pull qwen3.5:4b
python measure.py
```

## My results

Laptop: AMD Radeon integrated graphics, 14.8 GB RAM, model Qwen3.5 4B.

| Run | Time | Tokens | Energy (15–45 W) | CO₂ (169 g/kWh) |
|-----|------|--------|------------------|-----------------|
| No thinking | 10.7 s | 69 | 0.045–0.134 Wh | 0.008–0.023 g |
| Thinking, capped at 300 tokens | 42.4 s | 300 | 0.177–0.53 Wh | 0.030–0.090 g |
| Thinking, full run (manual) | 777 s | 3,975 | 3.2–9.7 Wh | 0.55–1.6 g |

The laptop power (15–45 W) is an **assumption**, not measured, so the energy is
a range. Thinking generates far more tokens, so it costs far more.

## Context: cloud chatbots (published estimates, short query)

| Source | Estimate |
|--------|----------|
| Gemini median prompt (Google, measured) | ~0.24 Wh |
| Epoch AI | ~0.3 Wh |
| ChatGPT average (stated, no method) | ~0.34 Wh |
| GPT-4o short query (benchmark) | ~0.43 Wh |
| Reasoning / long prompts | 10–29 Wh |

Comparing a laptop to the cloud is not exact (different models, hardware and
grid). This is an order-of-magnitude illustration, not a head-to-head.

## When AI is the lighter option (example)

Weather forecasting. GraphCast, a neural network, makes a 10-day forecast in
under a minute on one desktop, versus hours on a supercomputer, reportedly
~1,000× less energy per forecast (Financial Times). But training it was a
one-time cost: ~4,300 kWh (32 TPU v4 chips × 200 W × 4 weeks). One-time costs
exist on both sides: building the supercomputer, and training the model.

## Sources

- Projet Celsius — ChatGPT energy per query (compiles the Wh estimates; Google
  arXiv 2508.15734; benchmark arXiv 2505.09598)
- Electricity Maps — Austria 2025 grid intensity
- GraphCast — *Science*, doi 10.1126/science.adi2336; Google Cloud blog for TPU
  v4 power (~200 W per chip)

## Limits

Inference only. Cloud numbers are estimates that mix methods and dates. Laptop
power is assumed. Grids differ by country, so the CO₂ for cloud rows is an
illustration using Austria's grid.
