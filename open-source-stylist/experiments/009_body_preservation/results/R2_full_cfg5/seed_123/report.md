# Run outfit_001_hybrid_mask_crop_s123_506aa5b8a65f

- mode: **generate**  ·  created: 2026-06-15T18:58:50Z
- engine: `qie-2511`  ·  params: `{"steps": 20, "seed": 123, "width": 720, "height": 1024, "cfg": 5.0, "sampler": "euler", "scheduler": "simple"}`
- board: `hybrid_mask_crop` (sha256 542051b334f0…)

- output: `generated.png` (sha256 98826a4cf54a…), 210.09s

## Gates (limited instruments — not a product verdict)
- identity (face only): cosine=0.3733 → **FAIL**
- proportions (clothed silhouette — diagnostic): max_abs=14.06 framing_delta=1.69 → **FAIL**
- body (pose joints — clothing-robust): hipΔ=-8.26%  shoulderΔ=0.52%  ratioΔ=9.58%  (pose match 2.2°, vis 0.999)
- color[top]: dE=1.56 → **PASS**  ·  hueΔ=2.3°  chromaΔ=2.43  Lshift=5.41
- color[bottom]: dE=18.71 → **FAIL**  ·  hueΔ=102.9°  chromaΔ=10.3  Lshift=-0.28  ⚠hue unreliable (low chroma)
- color[shoes]: dE=10.53 → **FAIL**  ·  hueΔ=61.1°  chromaΔ=1.56  Lshift=-5.24  ⚠hue unreliable (low chroma)
- color[belt]: dE=9.22 → **FAIL**  ·  hueΔ=44.3°  chromaΔ=2.37  Lshift=6.26
- color[earrings]: dE=1.23 → **PASS**  ·  hueΔ=3.0°  chromaΔ=1.19  Lshift=-0.98

## Owner checkpoint
Review `generated.png` against the four criteria (identity, all items present, layering, colour/texture). The gates above are advisory only.
