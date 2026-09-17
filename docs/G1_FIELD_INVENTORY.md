# G1 field and acceptance inventory

Master plan phase-1 implement list: typed models, config, run/evidence manifests,
CLI skeleton, fixtures, schema tests, hosted fixture CI. Approval of G1 baseline
is documented in G1_DECISION_PROPOSAL.md; no assessment rules are enabled.

| Contract | MASTER_PLAN field mapping / implementation | Verification |
|---|---|---|
| RunManifest | All baseline fields in contracts.py; UUID replaces suggested timestamp/SHA ID under approved D12 baseline | timestamps, hashes, rule disabled, uniqueness and no overwrite |
| ProductPopulationRecord | family→listing.product_group; family_id→source_family_id; family_code→source_family_code; representative_sku/sku_role/PLP/PDP/source hash per listing; exact_sku/run_id per product; commerce/stock/ecom/variant observations per listing | merge duplicate SKU listings; distinct variants/case/wildcards; cross-run reject; conflicting values preserved |
| PDP | family/exact_sku in common envelope; all other baseline fields in facts.PdpFactRecord | exact field set, independent boolean claims, explicit measured unit/raw, referenced hash |
| EnergyGuide | exact_sku in envelope; all extraction fields in facts.EnergyGuideExtractionRecord | original hash, raw/normalized text separation, scale/ROI, typed quantities; no OCR correction |
| EPA | family in envelope; all EPA baseline fields in facts.EpaRecord | UPC missing state, market array, retrieval timezone, source hash; no certification inference |
| Assessment | All baseline fields plus assessment ID in contracts.py | same-run/group/SKU evidence references, no automatic legal conclusion, FTC HIGH + EPA MEDIUM preservation |
| Evidence | All baseline fields plus evidence ID/path; family→product_group | stored SHA, missing/corrupt bytes, traversal and symlink escape |
| Config/CLI | Five exact-key configs; init-run, validate, summarize; stdlib JSON/YAML subset | unsupported config/rules/run target rejected; canonical hash; file creation exclusive |
| Report | One exact SKU row; all assessments; FINDING records counted separately from affected distinct SKUs | overlapping group subtotals never determine global count; unevaluated counts do not assert compliance |

Current limitation: report input accepts only NOT_EVALUATED assessments by default;
synthetic transport tests use the fixture-only Python validation option. G2 must
introduce a versioned assessed bundle contract and rule engine before real findings
can be consumed. No live collection or dashboard is added by this inventory.

Full G1 acceptance record still requires review of hosted checkpoint coverage.
The CI verifies runtime field contracts, not a static type checker or package
installation. Dedicated static lint/type and installed-entrypoint checks are
not yet implemented; EXECUTION_GUIDE's broader CI quality checklist remains open.
This inventory does not label those missing checks PASS.
