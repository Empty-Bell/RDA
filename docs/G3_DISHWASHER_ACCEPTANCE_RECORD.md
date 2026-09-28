# G3 dishwasher family control acceptance — PASS, 2026-09-28

**Accepted scope:** the current 21 US Samsung dishwasher SKUs and the approved
ENERGY STAR publication, US EnergyGuide annual-energy, and printed-label model
identity controls. This accepts the dishwasher family control run, not the
whole G3 phase or a legal compliance conclusion for any product.

The user approved the printed EnergyGuide fixed-prefix rule for every product
family, including differing trailing star and PDP suffix lengths. All printed
model tokens were retained; one matching token establishes label/PDP model
inclusion. EPA Current registration remains a separate source check.

The hosted [model comparison](https://github.com/Empty-Bell/RDA/actions/runs/36393471484)
reports 21/21 PDP/label model matches. The [final assessment](https://github.com/Empty-Bell/RDA/actions/runs/36393493953)
has `READY_FOR_ASSESSMENT` with zero gaps and yields 21 SKUs: **12 PASS,
7 HIGH, 2 MEDIUM, 0 LOW**. Its 16 findings affect nine SKUs: seven
ENERGY STAR publication eligibility and seven EPA Current absence findings
on the same seven HIGH SKUs, plus two annual-energy mismatches. The
[canonical report](https://github.com/Empty-Bell/RDA/actions/runs/36393513013)
repeats the same 21 SKUs, grade counts and finding count, and the
[report dashboard workflow](https://github.com/Empty-Bell/RDA/actions/runs/36393526367)
succeeded.

The source bundle fingerprint across ENERGY STAR, numeric and model controls
is `sha256:2c6fb7e4481fdfaea884d3ff150aecfbaf999f59248cc9ff7bb57c257fa0afca`.
Numeric and model comparison share package SHA-256
`c8453ceeac9da50e84dd572f711345430a193552af55064db05a1db2d610d1c1`.
The nine visually reviewed label PDFs and their US annual values are recorded
by PDF SHA-256 in
[`evidence/g3-dishwasher-energyguide-visual-review.json`](evidence/g3-dishwasher-energyguide-visual-review.json).

The two MEDIUM models are `DW50T6060US/AA` (PDP/label 259 versus EPA 240
kWh/year) and `DW60R2014US/AA` (PDP/label 265 versus EPA 240 kWh/year).
Each HIGH model has no current EPA match but PLP logo, PDP logo and Specs
certification are present. The label model mismatch issue was removed from
those seven SKUs after visual review and the approved rule.

G3 overall remains open for the other product families. The mixed-family
GitHub Pages snapshot is a collection of family run results, not one unified
audit execution.
