# E-015 — garment-isolation method comparison (board-building) (2026-06-21)

Owner-directed: the universal pipeline auto-builds the board by isolating each garment from its ORIGINAL
image; grounded_sam (binary object mask) dropped pale buttons → gaps, and I was stacking repairs
(continuous-fill, button-recovery) on a fragile isolation. Compare isolation methods to find one that
builds clean tiles WITHOUT a repair cascade. Method: run each on outfit_001 originals; owner judges the tiles.

## Results (tiles in this folder)
| garment (original) | ATR human-parsing | grounded_sam |
|--------------------|-------------------|--------------|
| blouse (on model)  | **clean; BUTTONS preserved; model excluded** (`blouse_ATR.png`) | blouse ok, buttons fainter, binary mask |
| skirt (on model)   | clean; slit preserved (`skirt_ATR.png`) | (not run) |
| shoes (foot close-up) | fragments only, ~1.6% (`shoes_ATR.png`) | both wedges captured, some toe-skin (`shoes_groundedSAM.png`) |

## Findings (owner reviewed the tiles; verdict is the owner's)
- **ATR human-parsing** (the local Leffa ATR parser) isolates ON-MODEL garments cleanest: it is a SEMANTIC
  region parser (upper-clothes / skirt), so it preserves fine in-garment features (buttons, slit) and
  excludes the model — no per-feature repair (the button gap that needed `BUTTON_REPAIR` is gone).
- **grounded_sam** is better on the shoe close-up (ATR, a full-body parser, fragments it).
- **rembg / BiRefNet (matting) are the WRONG tool for on-model photos** by mechanism: matting separates
  foreground from background, so on a model it keeps the whole PERSON (garment + body + face) → violates
  V-REF-001. Matting only fits flat-lay product shots. (Asserted from the method, not run; verify if needed.)
- "coverage %" = fraction of image pixels the parser marked as that garment. skirt 9.4% = fine (skirt is
  part of the frame, tile clean); shoes 1.6% = the parser essentially FAILED on the close-up (shoes should
  be large), NOT "shoes are small."

## Direction (owner)
- Board stays **combined (mask + crop)** — proven to help QIE context/logic AND it is the configuration with
  good identity (6-cell hybrid 0.945 vs single-tile 0.40). The mask half should use the best isolator per
  element; the crop half stays for context.
- `_make_continuous` must be GENERAL (any garment's through-gaps), not skirt-only.
- Next idea (not built): an **intelligent board analyzer** — per element run multiple isolators, auto-select
  the best (face/skin leak, completeness, garment-identity, optional VLM), and that selection IS the board
  verification. Must be validated against owner judgment on these tiles.
