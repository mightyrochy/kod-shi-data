# E-003 — Conclusion

**Date:** 2026-06-11
**Status:** PASS

---

## Results

| Pair | Type | Cosine |
|------|------|--------|
| SP-01 (person_front vs person_two_view_front) | same | **0.9896** |
| DP-01 (person_front vs blouse_front / Model A) | different | 0.1188 |
| DP-02 (person_front vs skirt_front / Model B) | different | 0.1502 |
| DP-03 (Model A vs Model B) | different | 0.0927 |

- same_min = 0.9896
- diff_max = 0.1502
- gap = 0.8394 (protocol required ≥ 0.15)
- proposed threshold (midpoint) = **0.57**

All acceptance criteria met.

---

## Decision

Threshold **0.57** adopted as provisional identity gate cutoff:
- cosine >= 0.57 → same person (PASS)
- cosine < 0.57  → different person (FAIL)

Provisional because the gate's real operating condition (generated image vs
reference) is tested for the first time at E-005. Generated images may have
slightly degraded facial geometry, potentially reducing same-person cosine.
The gap here is so large (0.84) that even a 0.3 drop in same-person score
would still pass — but E-005 confirms this with real data.

---

## Observations

**CUDA not available for insightface:** onnxruntime ran on CPUExecutionProvider
only (`CUDAExecutionProvider` not in available providers). This means the identity
gate currently runs on CPU. For calibration this is irrelevant (accurate, just slow).
For production use (Stage 3+ pipeline) this warrants investigation:
- Check if `onnxruntime-gpu` is installed and matches the CUDA version on this machine
- Alternative: run insightface through ComfyUI (which does have GPU access) if a
  compatible node exists

This is an observation, not a blocker. Logged; not a Stage 1 gate requirement.

---

## Knowledge promoted

→ `knowledge/verified.md` V-ID-001
