# Northern-edge artifact test — supplement-ready robustness note

**Fix Round 2, item 6 · 2026-11-02 · Code:** `code/40_edge_test.py` ·
**Outputs:** `edge_test_poles.csv`, `edge_test_summary.json` (this folder).

## Question

Twenty of the aligned catalog's 52 dry poles sit at or north of
47.75 N, many on the domain's top row (49.75 N). Is that pile-up real
geography, or an artifact of the box: the detector takes the driest
cell in the domain, so when the true SPEI-1 minimum lies north of
50 N, in Canada, the in-box pole is forced onto the boundary rows?

## Test

The frozen Study-1-lineage detector (baseline definition: SPEI-1,
theta = 1.5, r = 4.0 degrees, f = 0.5, q = 0.10) was re-run on the
same SPEIbase v2.11 field (MD5-verified) with the northern boundary
moved from 50 N to 53 N (grid top row 52.75 N) and to 55 N (top row
54.75 N). Nothing else changed. The unexpanded run reproduces the 52
catalog months exactly, so the comparison is internal.

## Results

Catalog level: the expanded boxes return 58 months (north to 53 N)
and 73 months (north to 55 N), overlapping the 52 in 43 and 41 months
(Jaccard 0.642 and 0.488). The domain's northern boundary is therefore
itself a strong determinant of the catalog, on top of the threshold
and radius sensitivities the paper already reports.

Pole level, for the 20 baseline dry poles at or north of 47.75 N:

| Outcome under expansion | To 53 N | To 55 N |
|---|---|---|
| Dry pole stays in place (within 0.5 deg) | 6 | 5 |
| Dry pole moves north, short of the new edge | 8 | 10 |
| Dry pole moves onto the new top row | 3 | 1 |
| Month no longer qualifies | 3 | 4 |
| Dry pole moves south | 0 | 0 |

In each expanded run, 7 of the new catalog's dry poles sit on the new
top row.

## Verdict

The northern pile-up is substantially an edge artifact at the level
of pole location. Given more room to the north, the dry pole moves
north in 11 of the 17 (53 N box) and 11 of the 16 (55 N box) cases
where the month still qualifies, and never moves south: in those
months the SPEI-1 minimum lies in Canada, and the baseline pole is
its clipped position at the domain boundary. Only 5 to 6 of the 20
poles are stable at the same cell. Two qualifications keep the result
in proportion. First, the CDPE qualification is more robust than the
pole coordinates: 17 of the 20 months still qualify at 53 N and 16 of
20 at 55 N, because the buffer around the relocated pole still passes
the detector's gates. Second, the test does not indict the southern
or interior poles, and the catalog of record stays the 52: this note
is a robustness result, not a redefinition.

## Draft limitations paragraph (for the author's call)

> Seventh, the dry poles that sit along the northern boundary of the
> detection domain are boundary-clipped positions. When the domain is
> extended 3 to 5 degrees farther north on the same SPEIbase v2.11
> field, the dry pole moves north in 11 of the 16 to 17 cases in
> which the month still qualifies, and never moves south (Supplementary
> Information), so in those months the dipole's dry end is anchored
> in Canada, beyond the stated domain, and the northern dry-pole
> positions in Figure 2 should be read as at-or-beyond-boundary
> locations. The qualification of the months themselves is more
> robust: 16 to 17 of the 20 affected months remain CDPE months under
> the expanded domains. Domain extent joins threshold and radius as
> a catalog choice that conditions built on CDPE months inherit.

## Implication for Paper 2 (prerequisite note)

Any physical analysis keyed to dry-pole location (composites centred
on the pole, pole-relative sampling) must either extend its detection
domain north or treat northern dry poles as censored at the boundary;
event-centred sampling well inside the CONUS is unaffected.
