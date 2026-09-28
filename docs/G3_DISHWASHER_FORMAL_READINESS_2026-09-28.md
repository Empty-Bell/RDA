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
