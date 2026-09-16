# Phase 0 remaining acceptance work

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
Next: actual low-resolution and wildcard ROI regression evidence.
Reuse existing sanitized
fixtures and read compact projections/diffs. Use the existing model handoff guidance:
Sol medium for a new contract; Terra medium after the contract is fixed. Escalate
only a specific unresolved problem. Actions collection/parsing/tests use no LLM.

These are validation gates, not additional approved audit issue codes. D01/D07/D09/D10
in DECISIONS.md remain the authority for undecided comparison, corroboration,
certification and pipeline/document boundaries. Raw artifacts currently expire after
14 days; compact evidence does not replace original PDFs for future parser replay.
