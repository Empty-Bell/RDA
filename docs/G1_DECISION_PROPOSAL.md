# G1 approved baseline — bounded semantic approval

User approval: 2026-09-17, after explanation of product identity and independent
finding counts: "그렇지 모두 그렇게 진행해". All three presented criteria
(product identity, finding/affected-SKU counts, new run IDs/no overwrite) are
approved. Approval is limited to the G1 baseline below, not assessment rules.

| Decision | Approved G1 baseline | Deferred scope |
|---|---|---|
| D08 | One product record per `(run_id, exact_sku)`; preserve all group/source-family/listing provenance. Preserve exact SKU spelling. No implicit fuzzy or wildcard merge. | EPA model/wildcard matching and individual applicability in G2/G4 |
| D11 / relevant D02 portion | Product → multiple fact/evidence/assessment records. Preserve FTC and EPA findings independently, each referencing same-run/group/SKU evidence. | Rule priority and single-row display summary in G2 |
| D04 | Report product grain is exact SKU; finding count is assessment records, affected SKU count is distinct exact SKUs. A SKU with FTC HIGH and EPA MEDIUM therefore has two findings and one affected SKU. Group subtotals may overlap and must not be summed as global unique SKU counts. | Coverage denominator, severity summary and collection-completeness policy in G2 |
| D12 identifier portion | Each execution attempt gets a new UUID run_id; never overwrite raw files or bundles from prior run IDs. Keep GitHub run_id/run_attempt as separate execution provenance. | Durable raw store, retention length and restoration in G5/G6; 14-day CI artifacts are temporary only |

Approval of these G1 portions would not approve all of D02/D04/D08/D11/D12,
nor energy tolerances, OCR correction, missing certification, legal applicability,
publication or history policies. Implementation: population.py canonicalizes exact SKU records while preserving
distinct listing observations; report.py keeps all assessments in one SKU row
and computes finding/affected-SKU counts. Group findings use each assessment's
product_group; group product counts use listing membership. Cross-group subtotals
can overlap and must not be summed to derive global unique products.
Real evaluated findings remain disabled until G2; synthetic tests validate counts.

No further confirmation of these three criteria is required. G1 field inventory
and hosted acceptance review remain separate implementation checks.
