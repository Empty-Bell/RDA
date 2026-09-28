# G3 dishwasher formal readiness — BLOCKED, 2026-09-28

The latest successful candidate chain contains 21 exact dishwasher SKUs.
Its final assessment artifact reports 14 PASS and seven HIGH, but it cannot
be accepted as a final control result yet. Direct replay of the saved control
inputs found:

| Gap | Exact-SKU count | Why it matters |
|---|---:|---|
| US EnergyGuide annual value not selected | 15 | The PDP/label numeric comparison is `NOT_COMPARABLE`, yet 14 of these models are displayed as PASS. Eight have no extracted energy candidate and seven have only unclassified candidates. |
| OCR-only model mismatch without visual confirmation | 7 | The model comparison says `DIFFERENT` from raw OCR patterns and feeds a HIGH issue. These PDFs are not covered by the one approved visual correction. |
| Control source execution ID not carried into all three inputs | global | The final assessment joins the latest successful ENERGY STAR, numeric and model artifacts from different workflow generations; it cannot prove a single source run. |

The saved input runs reviewed were [ENERGY STAR 36361356843](https://github.com/Empty-Bell/RDA/actions/runs/36361356843),
[numeric 36359921822](https://github.com/Empty-Bell/RDA/actions/runs/36359921822),
[model 36361380916](https://github.com/Empty-Bell/RDA/actions/runs/36361380916),
and [final assessment 36361915525](https://github.com/Empty-Bell/RDA/actions/runs/36361915525).
The existing [report 36362073581](https://github.com/Empty-Bell/RDA/actions/runs/36362073581)
and its published snapshot are historical candidate outputs, not accepted
G3 results. A successful workflow status on those runs establishes that the
scripts executed; it does not close these evidence gaps.

The final-assessment workflow now writes an explicit `readiness.json` and
stops before creating a new assessment/report when a required value, visually
unconfirmed mismatch, or source-run binding is missing. The next concrete
work is to bind all controls to one immutable comparison package, review the
US EnergyGuide region and annual value for the eight unique unresolved PDF
groups, and replay all printed label model tokens with visual review where
OCR is uncertain. Once complete, rerun the control chain, validate all 21
models and only then update the public dashboard grades.

No new severity or issue code is assigned to the missing observations. A
source gap cannot be silently interpreted as PASS or HIGH.

## Follow-up: visual label review

Nine distinct source-label PDFs were visually reviewed. US-panel annual values for all 21 SKUs are keyed by PDF SHA-256 in [`evidence/g3-dishwasher-energyguide-visual-review.json`](evidence/g3-dishwasher-energyguide-visual-review.json). A replay against the saved package finds 20 PDP/label annual pairs equal and one PDP value absent. `DW50T6060US/AA` and `DW60R2014US/AA` have label/PDP values of 259 and 265 kWh/year versus 240 kWh/year in the EPA candidate rows. Under the approved G3 numeric rule these are MEDIUM candidates, pending hosted replay.

All seven previous model HIGH candidates now have visually verified printed patterns. One source prints `DW80BB7070*` for PDP `DW80BB707012AA`; another prints `DW80CG54******` for PDP `DW80CG5450SRAA`. The approved refrigerator prefix rule is family-specific. The dishwasher outcome awaits the user's trailing-wildcard decision; no model grade is changed yet.

The source-match report and comparison package now require byte-identical EPA and label inputs. ENERGY STAR, numeric and model controls carry a shared collection-plus-match fingerprint; the comparison controls also carry the exact package SHA-256. The final gate checks these before issuing a report. Hosted numeric comparison [36387187973](https://github.com/Empty-Bell/RDA/actions/runs/36387187973) completed with 21/21 US label values, 20 equal PDP/label pairs, one missing PDP value, and two label/EPA differences. Final readiness [36387214479](https://github.com/Empty-Bell/RDA/actions/runs/36387214479) is BLOCKED only on the seven dishwasher model-pattern suffix decisions. The follow-up assessment run [36387784389](https://github.com/Empty-Bell/RDA/actions/runs/36387784389) passed its workflow after tightening the missing-PDP rule, while formal readiness remains BLOCKED.

## Closed after user approval

The user approved the shared printed-label fixed-prefix rule across product
families, including unequal trailing-star and PDP suffix lengths. The hosted
[model comparison](https://github.com/Empty-Bell/RDA/actions/runs/36393471484)
now matches all 21 dishwasher PDP models to at least one visually reviewed
label token. [Final readiness](https://github.com/Empty-Bell/RDA/actions/runs/36393493953)
has zero gaps. The accepted dishwasher family result is recorded in
[G3_DISHWASHER_ACCEPTANCE_RECORD.md](G3_DISHWASHER_ACCEPTANCE_RECORD.md).
