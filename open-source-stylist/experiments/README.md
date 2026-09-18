# Experiment index

Experiments are records, not a single runnable pipeline. Completed runners may
depend on the contracts and prompts that existed when their outputs were created.
Their saved data remains evidence; rerunning old GPU phases is not assumed valid.

| Experiment | Status | Current meaning |
|---|---|---|
| E-001 | Closed | Segmentation masks and source mask evidence |
| E-002 | Closed | Preliminary color-distance calibration |
| E-003 | Closed | ArcFace calibration |
| E-004 | Closed | Proportion-metric calibration |
| E-005 | Closed, historical | Variance baseline under the old task prompt |
| E-006 | Closed, historical | Resolution comparison under the old task prompt |
| E-007 first attempt | Invalid, preserved | Invalid board; never use as evidence |
| E-007 v2 | Supplement measured | Original A/B mixed; hybrid fixes buttons and shoes, but color remains open |
| E-008 | Closed, historical | Full product photos vs old masked board; summary only |

The `hybrid_mask_crop` board and corrected outfit layout are prepared as new inputs,
but no new generation experiment is declared complete until it has its own record.
