# Run outfit_001_hybrid_mask_crop_s42_7e2f8d969298

- mode: **generate**  ·  created: 2026-06-15T16:13:00Z
- engine: `qie-2511`  ·  params: `{"steps": 20, "seed": 42, "width": 720, "height": 1024, "cfg": 5.0, "sampler": "euler", "scheduler": "simple"}`
- board: `hybrid_mask_crop` (sha256 542051b334f0…)

- output: `generated.png` (sha256 867f86516aed…), 200.83s

## Gates (limited instruments — not a product verdict)
- identity (face only): cosine=0.348 → **FAIL**
- proportions (clothed silhouette — diagnostic): max_abs=13.28 framing_delta=2.04 → **FAIL**
- body (pose joints — clothing-robust): hipΔ=-28.72%  shoulderΔ=-16.3%  ratioΔ=17.44%  (pose match 10.7°, vis 0.999)
- color[top]: SKIP_SANITY
- color[bottom]: SKIP_SANITY
- color[shoes]: dE=4.45 → **WARN**  ·  hueΔ=14.9°  chromaΔ=3.85  Lshift=1.8  ⚠hue unreliable (low chroma)
- color[belt]: SKIP_SANITY
- color[earrings]: dE=2.77 → **PASS**  ·  hueΔ=7.4°  chromaΔ=1.64  Lshift=-0.49

⚠ sanity flags: ['top', 'bottom', 'belt']

## Owner checkpoint
Review `generated.png` against the four criteria (identity, all items present, layering, colour/texture). The gates above are advisory only.
