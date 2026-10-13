# E-016 — general board builder, smoke run on outfit_001

**Status:** protocol written 2026-06-23 BEFORE running (METHODOLOGY §2).

**Goal:** verify the rewritten general builder (`system/board.py` + `system/garment.py`) produces the target
combined (mask + crop) board on outfit_001 WITHOUT any per-garment hardcoding — method chosen from the
image, single-piece continuity from geometry, thin gross-error guard.

**Inputs (canonical originals, `outfit_package.json`):** blouse_front.webp, skirt_front.webp,
shoes_wedge.webp. Labels passed as the board labels ("blouse front", "skirt front", "shoes"). Belt +
earrings are accessories -> deferred (not on this board).

**Procedure:** `run_board.py` calls `board.build([...])` only (no QIE). Saves board.png, per-garment
isolate tiles (mask + crop + raw mask), and board_report.json (method + guard metrics per garment).

**Owner checkpoint (verdict is the owner's):** does board.png match the target — blouse isolated cleanly
with buttons and model excluded; skirt isolated with the slit; both shoes captured; crops give context?
Which isolation method did the builder pick per garment, and did the guard pass all three?

**Expected by design (to be confirmed, not asserted):** blouse/skirt -> ATR (on-model/product, clean
region); shoes close-up -> ATR fails -> GroundingDINO+SAM fallback. No garment flagged.
