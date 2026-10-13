# E-004 — Conclusion

**Date:** 2026-06-11
**Status:** PASS

---

## Results

| Pair | Type | shoulder% | waist% | hip% | max_abs% |
|------|------|-----------|--------|------|----------|
| SAN-00 | sanity (same mask) | 0.0 | 0.0 | 0.0 | **0.00** |
| NAT-01 | natural variation | -0.10 | -0.09 | -0.35 | **0.35** |
| SYN-10 | synthetic +10% | 10.11 | 10.07 | 10.19 | **10.19** |
| SYN-20 | synthetic +20% | 20.18 | 20.15 | 20.08 | **20.18** |
| SYN-30 | synthetic +30% | 29.78 | 30.22 | 30.01 | **30.22** |

- natural ceiling = 0.35%
- synthetic floor = 10.19%
- gap = 9.84% (protocol required >= 5%)
- proposed threshold = **5.3%**

All acceptance criteria met.

---

## Decision

Threshold **5.3%** adopted as provisional proportions gate cutoff:
- max_abs_change_pct <= 5.3% → PASS (proportions preserved)
- max_abs_change_pct > 5.3%  → FAIL (proportions distorted)

Provisional: calibrated on natural photo-to-photo pairs. Real generated images
may have pose/scale variation not seen here; final threshold confirmed at E-005.
The gap (9.84%) leaves substantial headroom.

---

## Observations

**Gate is remarkably stable:** profiles nearly identical across two photos of the
same person at different scales (height 1267px vs 634px), confirming the
normalization works as intended. Per-zone accuracy on synthetic tests: SYN-10
measured 10.11–10.19% (expected 10%), SYN-30 measured 29.78–30.22% (expected 30%).
The gate behaves as a reliable linear ruler.

**Natural variation is very low (0.35%):** the two photos show the same person
in nearly identical upright posture. Poses with arms raised or significantly
different stances could produce higher natural variation — this is not yet tested.
In V1, generated images are expected to preserve the input pose, so low natural
variation is the correct operating condition.

---

## Knowledge promoted

-> knowledge/verified.md V-PROP-001
