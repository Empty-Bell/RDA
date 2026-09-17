# G2 refrigerator observational pilot

Status: implementation checkpoint, G2 RUNNING; no G2a–e acceptance yet.
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
