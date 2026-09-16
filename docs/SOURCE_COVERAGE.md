# Source coverage: reconnaissance versus full collection

Phase 0 is RUNNING. Successful source reconnaissance is not full per-model
fact collection, EPA certification matching or compliance PASS.

| Product group | Latest verified listing SKU snapshot | Individually verified PDP samples | Label samples | EPA access/schema |
|---|---:|---:|---:|---|
| Refrigerator | 75 | 1 | 1 | metadata + 3 generic sample rows |
| Dishwasher | 21 | 1 | 1 | metadata + 3 generic sample rows |
| Clothes Washer | 37 | 2 (combo/front-load) | 2 | metadata + 3 generic sample rows |
| Television | 167 | 1 | 1 | metadata + 3 generic sample rows |
| Range | 58 | 1 electric | OUT_OF_RECON_SCOPE (EPA-only) | metadata + 3 generic sample rows |
| Cooktop | pending hosted observation | pending | OUT_OF_RECON_SCOPE (EPA-only) | pending independent validation |

Listing snapshots include source variants and source-backed PDP URLs; they do not
mean that each linked PDP has been visited. Counts are historical observations,
not fixed production constants. See each product group's source contract for run IDs.

EPA generic sample rows can belong to other brands/product types. No Samsung SKU
candidate lookup has been performed. Complete EPA snapshot/pagination, product-type
applicability, current certification, markets, wildcard/UPC matching and claim
consistency are later contracts. Pipeline and parser errors never become no-candidate
or compliance PASS.

Full per-SKU PDP/label/EPA collection is downstream of source-contract discovery and
requires coverage/provenance gates. Remaining G0 source/quality/runtime acceptance
items must be verified before Phase 1; discovery of all 11 families alone does not
automatically close G0. Large raw artifacts currently expire after 14 days.
