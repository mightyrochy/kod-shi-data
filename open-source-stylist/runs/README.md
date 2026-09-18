# runs/ — ephemeral scratch output (git-ignored)

Per-run output of `python -m system.run_slice` and of `run_slice`-based runners.
Each run creates `<outfit>_<board>_s<seed>_<request_id>/` containing `generated.png`,
`manifest.json` (input hashes + filled workflow + gate results), `report.md`, and `masks/`.

**This is throwaway working output.** Everything here is ignored by git (see
`.gitignore`) and is safe to delete at any time — it is NOT the experimental record.

The canonical record of a study lives in `experiments/NNN_name/results/` (tracked):
protocolled runners copy the outputs they need there. Unfamiliar hash-named folders in
this directory are leftover ad-hoc runs and can be removed without losing anything.
