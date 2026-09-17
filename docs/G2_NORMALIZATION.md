# PDP source normalization, first increment

Scope: source encoding only. No compliance comparisons, issue codes, EPA match,
OCR correction, applicability or representative claim consensus is introduced.
Implementation: src/regaudit/normalization.py; tests: checks/g1/test_normalization.py.
Live pilot integration remains next work; existing pilot raw facts are unchanged.

Each normalized channel contains an Observation plus reason and unmodified raw
input. Annual energy requires a single source string with an explicit kWh/yr or
kWh/year unit. Bare numbers, power W, per-cycle measures, multiple candidates or
unsupported formatting remain NOT_OBSERVED. Capacity accepts only the observed
Total Capacity (cu. ft.) field with a single bare number or cu. ft. suffix; it does
not convert other capacities or infer label/PDP equivalence. Source field name
and value are retained in measurement.raw. Decimal parsing introduces no rounding
policy or discrepancy tolerance.

Boolean/Y/N/Yes/No/True/False flags normalize within each source channel separately.
Missing channel, null, numeric 0/1, keywords, unknown encoding or contradictory
flags remain NOT_OBSERVED with raw/reason. Explicit false remains VALUE false.
PLP true and PDP spec false are preserved simultaneously; no winning channel is
selected. Structured inputs must come from G0's product-only energy-star-field
projection, not arbitrary rendered text or nonclaim flag fields.

Fourteen new tests cover explicit/unknown/conflicting source flags, zero annual
energy, unit ambiguity, missing/multiple measurements, capacity field units and
nonmutation. The actual sanitized refrigerator claim fixture supplies source
flags; synthetic boundary inputs are labeled by test names. G1's remaining
identity/evidence/CLI regressions stay enabled; normalization alone cannot close G2.

The offline CI verifies source helpers and static/installed CLI quality on both
Python versions, without another browser/source scrape. The deployed application
still has no model/API runtime dependency.

Hosted checkpoint PASS: run 35174268354 at 55f2f4a; Python 3.11.16 and 3.12.14
each passed 94 fixture cases without skips and 15 quality/installed CLI checks.
Downloaded reports/wheels verified; docs/evidence/g2-normalization-recon.json
records hashes and expiry. G2 full gate remains NOT_EVALUATED.
