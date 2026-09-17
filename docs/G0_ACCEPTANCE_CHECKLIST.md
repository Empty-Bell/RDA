# Phase 0 remaining acceptance work

Consolidated evidence, phase-specific gaps and next bounded work are recorded in
[G0_REVIEW.md](G0_REVIEW.md). Completed common probes remain bounded PASS;
EPA active-version/source routing and official applicability provenance still
need closure before full G0. No later-phase OCR/rules requirement is silently
treated as completed by this review.

All product-family discovery must be followed by common contract acceptance.
Phase 0 stays RUNNING until the relevant hosted evidence and open questions have
been reviewed; downstream full per-SKU collection and compliance are not performed here.

| Next task | Intermediate artifact | Verification before acceptance |
|---|---|---|
| Independent public claim and PDP identity contracts | Product-only rendered badge/structured claim fixtures, title/commerce mapping | Keep PLP flag, rendered badge, PDP structured claim and spec claim separate; exact SKU, contradictory and unobserved cases; actual hosted browser evidence |
| EnergyGuide field quality | Original PDF hashes, embedded text/OCR field provenance, low-resolution/wildcard regression fixtures | Distinguish numeric energy, model identity, capacity and label reference range; preserve disagreement and unreadability; do not invent comparison tolerance or new issue codes |
| EPA query/type/current-source contract | Dataset-specific type/market/update observations, bounded pagination/query fixtures and open questions | Reject incomplete/error/empty diagnostic responses as candidate absence; retain wildcard, UPC omission and variant ambiguity; no certification rule until semantics are fixed |
| Hosted runtime freeze and recovery | Transitive dependency lock, OCR model checksums, verified Actions pins, source failure records | Cold ubuntu-24.04 x64 PDF/OCR/browser probes and full source regression; no credentials in artifacts; bounded retries preserve failures; desktop UA does not prove permanent 403 resolution |
| Consolidated G0 review | Updated Samsung/EPA/runtime contracts, coverage and unresolved decision list | Each requirement links to hosted evidence; unresolved semantics are explicitly retained; discovery PASS never becomes full collection or compliance PASS |

Bounded raw claim/identity reconnaissance passed in run 35160456564 (126 tests,
12 source legs); see PUBLIC_CLAIM_IDENTITY_CONTRACT.md. Bounded primary PDP logo
attribution and exact inline product-flag extraction passed in run 35162114501 (143 tests,
12 source legs); see CLAIM_ATTRIBUTION_SOURCE_CONTRACT.md. Unsupported surfaces
and unobserved flags remain unknown. Bounded EnergyGuide field/coordinate
reconnaissance passed in run 35163198471 (154 tests, 12 source legs, five label
fixtures); see ENERGYGUIDE_FIELD_SOURCE_CONTRACT.md and energyguide-field-recon.json.
Extraction health is separate from canonical annual selection and identity matching.
Bounded controlled low-resolution/model-like ROI probes passed in run 35164831308
(165 tests, 12 source legs, five labels); see ENERGYGUIDE_QUALITY_CONTRACT.md and
energyguide-quality-recon.json. Color and grayscale/Otsu retries retain independent
outputs; wildcard disagreement is never silently corrected. Naturally degraded
source PDFs, the complete glyph/wrong-model matrix and approved corroboration
semantics remain open. Bounded EPA query/catalog/type/update extraction passed in
run 35165687365 (nine datasets, 12 query tests); full source regression run
35165687343 passed 177 tests and 12 source legs. See EPA_QUERY_SOURCE_CONTRACT.md
and epa-query-recon.json. Declared query completeness is separate from full EPA
coverage, type/market applicability, active-version exclusivity and current
certification. D09 remains OPEN. Bounded application runtime freeze and controlled
recovery passed run 35166865310 (two cold jobs, 180 tests); full source 35166865304,
EPA 35166865352 and runner probe 35166865316 passed. See RUNTIME_FREEZE_CONTRACT.md
and runtime-freeze-recon.json. Hashed package/build/model resources and Node24
Actions are pinned; image/system libraries remain hosted inputs. Controlled-copy
recovery is separate from generic source/WAF recovery. Consolidated G0 review is
now recorded in G0_REVIEW.md; full G0 remains NOT_EVALUATED. Next: official EPA
active-version and alternate product-type source-routing evidence.
Reuse existing sanitized
fixtures and read compact projections/diffs. Use the existing model handoff guidance:
Sol medium for a new contract; Terra medium after the contract is fixed. Escalate
only a specific unresolved problem. Actions collection/parsing/tests use no LLM.

These are validation gates, not additional approved audit issue codes. D01/D07/D09/D10
in DECISIONS.md remain the authority for undecided comparison, corroboration,
certification and pipeline/document boundaries. Raw artifacts currently expire after
14 days; compact evidence does not replace original PDFs for future parser replay.
