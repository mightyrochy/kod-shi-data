# Run outfit_001_hybrid_mask_crop_s123_eb9098d721a3

- mode: **generate**  ·  created: 2026-06-15T16:12:00Z
- engine: `qie-2511-lightning`  ·  params: `{"steps": 4, "seed": 123, "width": 720, "height": 1024, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"}`
- board: `hybrid_mask_crop` (sha256 542051b334f0…)

- output: `generated.png` (sha256 d4d4b4953c88…), 40.41s

## Gates (limited instruments — not a product verdict)
- identity (face only): cosine=0.7597 → **PASS**
- proportions (clothed silhouette — diagnostic): max_abs=12.6 framing_delta=3.18 → **FAIL**
- body (pose joints — clothing-robust): hipΔ=-9.0%  shoulderΔ=-2.48%  ratioΔ=7.19%  (pose match 2.1°, vis 0.999)
- color[top]: dE=1.67 → **PASS**  ·  hueΔ=5.9°  chromaΔ=1.08  Lshift=-7.07
- color[bottom]: dE=3.76 → **WARN**  ·  hueΔ=5.6°  chromaΔ=5.13  Lshift=1.82
- color[shoes]: dE=3.48 → **WARN**  ·  hueΔ=15.7°  chromaΔ=2.58  Lshift=7.58  ⚠hue unreliable (low chroma)
- color[belt]: dE=5.42 → **FAIL**  ·  hueΔ=1.7°  chromaΔ=7.48  Lshift=11.76
- color[earrings]: dE=5.64 → **FAIL**  ·  hueΔ=2.0°  chromaΔ=12.46  Lshift=-11.95

## Owner checkpoint
Review `generated.png` against the four criteria (identity, all items present, layering, colour/texture). The gates above are advisory only.
