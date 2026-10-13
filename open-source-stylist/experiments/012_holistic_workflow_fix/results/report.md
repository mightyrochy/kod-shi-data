# Run outfit_001_hybrid_mask_crop_s42_d8bce7d4b9af

- mode: **generate**  ·  created: 2026-06-20T11:28:10Z
- engine: `qie-2511`  ·  params: `{"steps": 20, "seed": 42, "width": 720, "height": 1024, "cfg": 4.0, "sampler": "euler", "scheduler": "simple", "denoise": 1.0}`
- board: `hybrid_mask_crop` (sha256 542051b334f0…)

- output: `generated.png` (sha256 5617fbcd3d67…), 193.51s

## Gates (limited instruments — not a product verdict)
- identity (face only): cosine=0.9191 → **PASS**
- proportions (clothed silhouette — diagnostic): max_abs=None framing_delta=None → **NO_PERSON_MASK**
- body (pose joints — clothing-robust): hipΔ=-6.96%  shoulderΔ=-2.73%  ratioΔ=4.54%  (pose match 4.2°, vis 0.999)

## Owner checkpoint
Review `generated.png` against the four criteria (identity, all items present, layering, colour/texture). The gates above are advisory only.
