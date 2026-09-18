# Run outfit_001_hybrid_mask_crop_s42_294136aed237

- mode: **generate**  ·  created: 2026-06-15T16:10:56Z
- engine: `qie-2511-lightning`  ·  params: `{"steps": 4, "seed": 42, "width": 720, "height": 1024, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"}`
- board: `hybrid_mask_crop` (sha256 542051b334f0…)

- output: `generated.png` (sha256 25639962c1c5…), 40.44s

## Gates (limited instruments — not a product verdict)
- identity (face only): cosine=0.8056 → **PASS**
- proportions (clothed silhouette — diagnostic): max_abs=14.31 framing_delta=3.28 → **FAIL**
- body (pose joints — clothing-robust): hipΔ=-8.82%  shoulderΔ=-0.82%  ratioΔ=8.77%  (pose match 3.0°, vis 0.999)
- color[top]: dE=2.15 → **PASS**  ·  hueΔ=5.3°  chromaΔ=2.82  Lshift=-10.75
- color[bottom]: dE=3.36 → **WARN**  ·  hueΔ=5.8°  chromaΔ=4.23  Lshift=5.35
- color[shoes]: dE=5.4 → **FAIL**  ·  hueΔ=26.4°  chromaΔ=4.06  Lshift=11.56  ⚠hue unreliable (low chroma)
- color[belt]: dE=5.7 → **FAIL**  ·  hueΔ=1.1°  chromaΔ=7.87  Lshift=8.39
- color[earrings]: dE=0.83 → **PASS**  ·  hueΔ=0.1°  chromaΔ=0.2  Lshift=-5.36

## Owner checkpoint
Review `generated.png` against the four criteria (identity, all items present, layering, colour/texture). The gates above are advisory only.
