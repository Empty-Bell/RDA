# G1 decision proposal — review required before stable contracts

Technical drafts do not close D01–D12. These proposals are concrete enough to
review but remain disabled as production policy until explicit approval.

| Decision | Proposed G1 baseline | Deferred scope |
|---|---|---|
| D08 | One product record per `(run_id, exact_sku)`; preserve all group/source-family/listing provenance. Preserve exact SKU spelling. No implicit fuzzy or wildcard merge. | EPA model/wildcard matching and individual applicability in G2/G4 |
| D11 / relevant D02 portion | Product → multiple fact/evidence/assessment records. Preserve FTC and EPA findings independently, each referencing same-run/group/SKU evidence. | Rule priority and single-row display summary in G2 |
| D04 | Report product grain is exact SKU; finding count is assessment records, affected SKU count is distinct exact SKUs. A SKU with FTC HIGH and EPA MEDIUM therefore has two findings and one affected SKU. Group subtotals may overlap and must not be summed as global unique SKU counts. | Coverage denominator, severity summary and collection-completeness policy in G2 |
| D12 identifier portion | Each execution attempt gets a new UUID run_id; never overwrite raw files or bundles from prior run IDs. Keep GitHub run_id/run_attempt as separate execution provenance. | Durable raw store, retention length and restoration in G5/G6; 14-day CI artifacts are temporary only |

Approval of these G1 portions would not approve all of D02/D04/D08/D11/D12,
nor energy tolerances, OCR correction, missing certification, legal applicability,
publication or history policies. The current synthetic fixture verifies only
record preservation and graph integrity. Metrics are not yet implemented.

No immediate user decision is needed to continue specialized fact schemas,
config validation and fixture CI. Explicit confirmation of the above baseline
will be needed before making the product/report contract stable and closing G1.
