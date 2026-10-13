"""Finalize a run's conclusion after human review.

Usage:
    python -m pipeline.confirm_run <run_id> [--verdict pass|fail] [--notes "..."]

What it does:
1. Reads conclusion/evaluation_draft.json (VLM output).
2. Shows it alongside the human-reviewable output path.
3. Applies the human verdict (override or confirm the VLM overall_pass).
4. Appends human notes to conclusion/notes.md.
5. Writes conclusion/evaluation.json (the final, reviewed record).
6. Marks the draft as consumed (renames to evaluation_draft_consumed.json).

The verdict flag overrides the VLM's overall_pass.
Without --verdict the VLM's overall_pass is kept (you are confirming, not overriding).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs" / "experiments" / "v1alpha"


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("Usage: python -m pipeline.confirm_run <run_id> [--verdict pass|fail] [--notes '...']")
        return 1

    run_id = args[0]
    run_dir = RUNS_DIR / run_id
    if not run_dir.is_dir():
        print(f"ERROR: run not found: {run_dir}")
        return 1

    draft_path = run_dir / "conclusion" / "evaluation_draft.json"
    final_path = run_dir / "conclusion" / "evaluation.json"
    notes_path = run_dir / "conclusion" / "notes.md"

    if final_path.exists():
        print(f"evaluation.json already exists for run {run_id}. Already confirmed.")
        return 0

    if not draft_path.exists():
        print(f"ERROR: no evaluation_draft.json found in {run_dir / 'conclusion'}")
        return 1

    with open(draft_path, encoding="utf-8") as f:
        draft = json.load(f)

    # -- parse args -----------------------------------------------------------
    verdict_override = None
    human_notes = ""
    i = 1
    while i < len(args):
        if args[i] == "--verdict" and i + 1 < len(args):
            v = args[i + 1].lower()
            if v not in ("pass", "fail"):
                print("ERROR: --verdict must be 'pass' or 'fail'")
                return 1
            verdict_override = v == "pass"
            i += 2
        elif args[i] == "--notes" and i + 1 < len(args):
            human_notes = args[i + 1]
            i += 2
        else:
            i += 1

    # -- build final evaluation -----------------------------------------------
    final = dict(draft)
    if verdict_override is not None:
        final["overall_pass"] = verdict_override
        final["_verdict_source"] = "human"
    else:
        final["_verdict_source"] = "vlm_confirmed"

    if human_notes:
        final["_human_notes"] = human_notes

    # -- show summary ---------------------------------------------------------
    print(f"Run {run_id} — confirming conclusion")
    print(f"  Output: {run_dir / 'output' / 'output.png'}")
    print()
    for verdict_key, notes_key in [
        ("identity_preserved",  "identity_notes"),
        ("outfit_items_present","items_notes"),
        ("outfit_logic_followed","logic_notes"),
        ("colors_textures_match","color_notes"),
    ]:
        v = final.get(verdict_key)
        n = final.get(notes_key, "")
        print(f"  [{'PASS' if v else 'FAIL'}] {verdict_key.replace('_',' ').upper()}")
        if n:
            print(f"         {n}")
    print()
    overall = final.get("overall_pass", False)
    src = final.get("_verdict_source", "")
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}  (source: {src})")
    if human_notes:
        print(f"  Human notes: {human_notes}")
    print()

    # -- write final ----------------------------------------------------------
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    # -- append to notes.md ---------------------------------------------------
    if human_notes:
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Human review\n\n{human_notes}\n")

    # -- mark draft consumed --------------------------------------------------
    draft_path.rename(draft_path.parent / "evaluation_draft_consumed.json")

    print(f"Saved: {final_path}")
    print(f"Run {run_id} conclusion finalized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
