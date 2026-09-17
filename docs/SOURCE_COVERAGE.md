# Source coverage: reconnaissance versus full collection

Phase 0 / G0 source reconnaissance is accepted; see G0_ACCEPTANCE_RECORD.md.
Successful source reconnaissance is not full per-model
fact collection, EPA certification matching or compliance PASS.

| Product group | Latest verified listing SKU snapshot | Individually verified PDP samples | Label samples | EPA access/schema |
|---|---:|---:|---:|---|
| Refrigerator | 75 | 1 | 1 | metadata + 3 generic sample rows |
| Dishwasher | 21 | 1 | 1 | metadata + 3 generic sample rows |
| Clothes Washer | 37 | 2 (combo/front-load) | 2 | metadata + 3 generic sample rows |
| Television | 167 | 1 | 1 | metadata + 3 generic sample rows |
| Range | 58 | 1 electric | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Cooktop | 20 | 2 (gas/radiant electric) | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Clothes Dryer | 54 | 2 (combo/standalone) | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Ventilating Hood | 16 | 1 | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Monitor / Display | 76 | 1 | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Computer | 24 (Galaxy Book + Chromebook union) | 2 (Windows/Chrome OS) | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows per source leg |
| Tablet | 50 | 1 (Wi-Fi / 256 GB) | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |

Listing snapshots include source variants and source-backed PDP URLs; they do not
mean that each linked PDP has been visited. Counts are historical observations,
not fixed production constants. See each product group's source contract for run IDs.
Computer has two separately linked consumer listing sources; its union retains SKU
provenance without treating repeated generic EPA queries as additional certification coverage.

EPA generic sample rows in this historical discovery table can belong to other
brands/product types. Additional bounded literal Samsung-brand scans completed
across nine datasets in run 35165687365; see EPA_QUERY_SOURCE_CONTRACT.md and
epa-query-recon.json. These are complete declared brand queries, not a complete
cross-brand EPA snapshot or retail-SKU certification matching coverage. Exact model
probes use EPA rows as seeds, not PDP identity. Product-type applicability, current
certification, markets, wildcard/UPC matching and claim consistency remain
NOT_EVALUATED. Pipeline/parser errors never become no-candidate or compliance PASS.

Full per-SKU PDP/label/EPA collection is downstream of source-contract discovery and
requires coverage/provenance gates. Remaining G0 source/quality/runtime acceptance
items must be verified before Phase 1; discovery of all 11 families alone does not
automatically close G0. Large raw artifacts currently expire after 14 days.
