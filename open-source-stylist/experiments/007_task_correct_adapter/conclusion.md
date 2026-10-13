# E-007 v2 conclusion

**Closed:** 2026-06-14
**Owner review:** original A/B complete; hybrid supplement pending
**Decision:** original A/B mixed; hybrid is the provisional next candidate

## Owner verdict

Both crop methods have better and worse outputs depending on the detail. The blouse
shade is visibly different from the original reference in both arms.

The masked board has an additional input defect: the blouse-front mask removes the
front buttons. That omission propagates into generation, so E-007 cannot be treated
as a clean test of mask isolation versus rectangular cropping for blouse structure.

## What remains valid

- Full product-photo contamination is absent in both E-007 v2 arms.
- Both arms preserve recognizable identity across all five seeds.
- The rectangular arm produces 5/5 clean measurement-mask sets; the masked arm
  produces only 1/5, so masked-arm color aggregates are not decision-grade.
- Neither arm produces the wedge sandals because the old layout wording was
  interpreted as bare feet. The layout file was corrected after this run.

## Hybrid supplement

A third frozen board, `hybrid_mask_crop`, was generated with the same five seeds,
workflow, person image, resolution, and sampling settings. It combines:

- corrected blouse-front mask with visible buttons + blouse-front rectangular crop;
- skirt-front mask + skirt-front rectangular crop;
- masked belt;
- masked + rectangular earrings;
- masked + rectangular wedge sandals.

The supplement also uses the owner-edited layout, so it tests the complete
corrected input rather than the board alone. It must not be used to claim that
one board construction method caused every difference.

### What improved

- Wedge sandals appear in 5/5 hybrid outputs; both original arms produced bare feet.
- The V neckline and a central row of blouse buttons are present in 5/5 outputs.
- All 5/5 hybrid measurement-mask sets pass sanity checks. The masked arm had
  only 1/5 fully usable sets, while the rectangular and hybrid arms have 5/5.
- Identity remains recognizable and above threshold in all five outputs.

### What did not improve enough

- The blouse still appears too pale/yellow relative to the supplied garment,
  despite the automatic top-color mean improving to dE 2.400.
- The silhouette-width diagnostic remains poor at 12.644%. This is better than
  masked crops at 15.632% but worse than rectangular crops at 5.828%; footwear
  and framing also changed, so this metric is not a body-shape verdict.
- Shoe color mean is dE 6.220. This is far better than the invalid bare-feet
  comparison near dE 29.7, but it remains outside the current fail threshold.

### Provisional decision

The hybrid input is the strongest candidate for the next iteration on garment
completeness: it fixes the missing-button input defect and produces the requested
footwear consistently. It is not an overall winner yet because blouse color and
silhouette fidelity remain unresolved. Final preference still requires owner
review of `results/three_way_contact_sheet.png`.
