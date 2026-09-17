# G2 refrigerator observational pilot

Status: first observational checkpoint PASS, G2 RUNNING; no G2a–e acceptance yet.
Hosted run 35173368182, tested code 59d973f, attempt 1, job 105049619026.
Listing snapshot: 41 groups / 75 exact SKUs; selected RF29DB9900QDAA PDP and
original EnergyGuide; complete observed Samsung-brand EPA scan: 101 rows.
93 evidence records/file hashes verified after downloading the artifact. Bundle
execution remains PARTIAL and assessments NOT_EVALUATED. Population/report SKU
sets match; mixed-run mutation rejected. See docs/evidence/g2-pilot-recon.json
for checkpoint, ZIP hash, expiry and limited-scope acceptance. These observed
counts are a snapshot, not production constants.
The user authorized Phase 2 after G1 PASS. This first increment reuses the tested
source_recon and epa_recon collectors; runtime/model costs are unchanged and
there are no LLM/API inference calls.

scripts/g2_smoke.py runs refrigerator listing/rendered tile/PDP/PDF reconnaissance
and complete literal Samsung-brand EPA scanning on one hosted job. It requires
both collector PASS reports with the current GitHub run/code identity. It then
adapts listing pages to canonical products, copies evidence into a fresh UUID
run directory, verifies hashes and same-run/group/SKU references and creates
bundle.json/report.json/checkpoint.json. Raw output creation is exclusive.
G1 configs remain the disabled schema baseline; the authorized pilot workflow
explicitly runs the source collectors, never enables the G1 assessment CLI.

Population includes representative plus all observed variants. Repeated requests
at one offset must have identical projected bytes; unique pages undergo G0's
population completeness/total/group checks. Each distinct page hash is retained
in listing provenance. Stock/ecommerce values are preserved without coercion.
Zero population, boundary duplicate groups, incomplete pagination, total drift,
missing variants, wrong representative/group/URL and cross-listing SKU overlap
have fixtures in checks/g2. These cases do not yet constitute the full G2a suite.

PDP and original parsed EnergyGuide are collected for ONE source-selected exact
SKU. The bridge must contain that exact SKU and the label URL must belong to its
Support record. Raw PDP claim/spec observations, original PDF, extraction text,
unselected field/layout candidates are linked as evidence. Annual energy,
capacity, label model and claim adjudication remain NOT_OBSERVED in typed facts
until their explicit normalization/selection contracts are implemented. This
does not discard the underlying observations: evidence preserves those raw fields.

EPA Samsung-brand dataset responses and their original hashes are copied as
dataset query CONTEXT, not evidence of a SKU certification match. There is no
EpaRecord for an unselected/unmatched row; no-candidate and eligibility are not
inferred. Dataset context alone cannot produce an EPA finding.

Bundle execution status is PARTIAL because most population SKUs have not had PDP
and label collection. Both sample domain assessments are NOT_EVALUATED. Report
zero finding counts mean zero recorded findings with evaluation disabled, not
healthy/compliant products. Pipeline checkpoint PASS only means this bounded
observational package was collected and validated. It cannot close G2 or permit
other product-group expansion.

Source URLs and projected response hashes identify each copied public projection;
pf/bridge JSON is sanitized public data, not the full original HTTP response.
Original PDF and EPA nonmetadata response bytes are preserved unmodified.
captured_at uses the pilot start timestamp as collection-session anchor; individual
per-response timestamps are not yet available from G0 collectors and are not
claimed. More precise per-request timing is remaining G2 collector work.

GitHub-hosted ubuntu-24.04 x64, pinned Python/runtime/bootstrap, realistic installed
Chromium user-agent, always-upload evidence with 14-day review retention. Failed
collectors/hash/graph checks make the workflow fail and retain a failed checkpoint.
No production dashboard, schedule or publication is introduced.

Next increments: per-SKU PDP collection/coverage and identity fixtures (including
redirect/selected variant mismatch), source-backed measure/claim normalization,
PDF/OCR golden corpus and decision proposals for D01–D04/D07/D09/D10, EPA matching,
versioned assessed bundles/rules, fixture dashboard, then full refrigerator gate.
No rule or new issue code is approved by collection success.

## Per-SKU PDP increment

The current pilot selects up to ten population SKUs deterministically: existing
PDF sample, one other representative, one variant, then remaining sorted SKUs.
The cap is a request budget, not a hardcoded population size or full coverage.
Each additional SKU gets a fresh page in the shared desktop Chromium context.
Final URL must be on Samsung US with that source SKU slug, current Product
JSON-LD identifiers must equal the exact SKU, and exactly one target Specs and
Support record must exist. Missing/contradictory identity is collection failure,
not automatic wrong-model/legal finding. Slash-to-hyphen spelling is permitted
only for Samsung URL slug checks; exact SKU keys/declarations remain unchanged.

Per-response timestamps and projected bridge hashes are recorded before
interpretation. Product snapshot, response/error metadata and raw PDP fields are
retained. Successful responses add typed PDP facts/evidence to the same run.
All sample attempts continue independently; any failed sampled SKU fails the
pilot checkpoint while retaining partial package/coverage for review.

pdp-coverage.json covers every population SKU exactly once with
VERIFIED_EXACT_IDENTITY, FAILED or NOT_ATTEMPTED. Counts sum to population_count;
attempted_count includes verified plus failed. This technical collection coverage
is not D04's future assessment/domain completion denominator. Unattempted and
failed SKUs do not disappear and are not counted as healthy. Label collection
still covers the original one SKU; EPA per-SKU matching and rules remain disabled.

checks/g2 now has 30 regression cases including redirects, wrong selected variant,
missing/invalid JSON-LD, contradictory MPN, duplicate/wrong Specs, source flag
preservation and coverage identity/count/status mutations. Live hosted verification
of this increment passed run 35173796328 (code 21b621a), attempt 1, job
105050931631. Population 75: verified 5, failed 0, not attempted 70.
Samples RF29DB9900QDAA, RF18A5101SR/AA (representative), RF18A5101MT/AA
(variant), RF18A5101S9/AA, RF22A4111SR/AA. Downloaded evidence 105 hashes
and population/coverage/report SKU sets verified; additional sample identity
replayed from copied raw observations. See docs/evidence/g2-pdp-coverage-recon.json.
These snapshot counts are not runtime constants; this does not close G2a.

## Expanded bounded PDP coverage checkpoint

The deterministic PDP budget increased from five to ten after normalized source
observations were connected to typed PDP facts. Hosted run 35175307189 at
d884b4c passed on an ubuntu-24.04 runner: all fixture regressions, collection,
bundle/evidence validation and artifact preservation succeeded. The collector exits
nonzero when any selected SKU has FAILED identity, so this success establishes no
failure among the selected bounded sample. It does not establish full population
coverage, label coverage beyond the original SKU, EPA certification matching or a
regulatory outcome. See docs/evidence/g2-pdp-coverage-expansion-recon.json.

Before expanding label retrieval, Support-declared document planning passed ten
fixture contracts on hosted Python 3.11 and 3.12 in run 35175865085. The plan
retains every exact-SKU HTTPS document candidate and marks a missing Support
document NOT_OBSERVED; it neither selects a canonical PDF nor parses a value.
