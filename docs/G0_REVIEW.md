# G0 consolidated review — 2026-09-17

Phase 0 remains RUNNING; full G0 is NOT_EVALUATED. This review does not approve
audit rules, program applicability or Phase 1 implementation. All D01–D12 remain
OPEN. Scope follows MASTER_PLAN Phase 0 and EXECUTION_GUIDE G0.

## Acceptance evidence

| Requirement | Bounded result / hosted evidence | Remaining boundary |
|---|---|---|
| All 11 listing contracts, variants, pagination and count grain | PASS: [12 source legs](https://github.com/Empty-Bell/RDA/actions/runs/35166865304); family contracts and SOURCE_COVERAGE.md | Historical listing inventories; representative PDP samples, not all linked models |
| Exact PDP identity and current structured endpoint | PASS for selected samples: same source run; PUBLIC_CLAIM_IDENTITY_CONTRACT.md and family contracts | Computer/Chromebook/Tablet use selected configuration + Specs endpoint; Support is not evaluated. Do not force an obsolete common bridge endpoint |
| Independent public claim provenance | PASS for supported product-only surfaces: [attribution run](https://github.com/Empty-Bell/RDA/actions/runs/35162114501) | Unobserved badge/unsupported inline flag stays unknown; no claim truth adjudication |
| Current EnergyGuide URL, download and field provenance | PASS for five actual label samples: [fields](https://github.com/Empty-Bell/RDA/actions/runs/35163198471), [controlled quality](https://github.com/Empty-Bell/RDA/actions/runs/35164831308) | No canonical annual selection/model matching. Controlled degradation is not naturally degraded PDF coverage |
| EPA access, schemas, query completion and error boundaries | PASS for nine configured datasets: [EPA queries](https://github.com/Empty-Bell/RDA/actions/runs/35165687365), [locked-runtime regression](https://github.com/Empty-Bell/RDA/actions/runs/35166865352) | Official catalog advertisement does not establish exclusive active version or product-type applicability; source-routing closure still required |
| Cold hosted runtime and isolated corruption recovery | PASS: [two cold jobs](https://github.com/Empty-Bell/RDA/actions/runs/35166865310), [separate probe](https://github.com/Empty-Bell/RDA/actions/runs/35166865316); 180 tests with installed dependencies | Managed image/system libraries remain variable; desktop UA success does not guarantee future access |
| Sanitized fixture path/byte integrity | PASS: [hosted review](https://github.com/Empty-Bell/RDA/actions/runs/35167790999), 92 manifest references checked against actual Ubuntu checkout bytes; docs/evidence/g0-integrity-review.json | This is repository integrity, not raw artifact availability, parser coverage or G0 promotion |

The fixture manifests distinguish committed LF bytes (`sha256` / `fixture_sha256`)
from retained historical capture bytes (`capture_bytes_sha256`). The initial
refrigerator projection has the analogous `projected_capture_bytes_sha256`.
Original artifact ZIP/PDF hashes are unchanged. Fully qualified repository paths
replace six ambiguous refrigerator basenames. No fixture facts were modified.
Windows diagnostics may use `--git-blobs`; hosted acceptance uses actual checkout
files without that option. Report errors remain FAIL and cannot promote G0.

## Work that must precede full G0 review

1. **EPA source routing / active version evidence.** Verify the official certified
   product directory and specification/version references for the configured
   datasets. Inspect alternate combo dataset `9jai-gs6t`, combo/stacked routes,
   the Ventilating Fans versus hood scope, cooking gas/electric boundaries and
   Notebook/Slate-Tablet routes. Save official URLs, retrieved public metadata,
   timestamps, hashes, schema and sanitized fixtures. Unsupported or unresolved
   routes remain explicitly blocked; a zero-row Samsung scan is not N/A.
2. **Official applicability provenance.** EXECUTION_GUIDE requires FTC/EPA
   official source, observation date and relevant location. Consolidate those
   references into a family applicability evidence table. Distinguish observed
   source scope from a proposed interpretation requiring D09 approval.
3. **Final contract closure.** Recheck the G0 normal/empty/pagination/missing-field/
   duplicate-variant/error fixture coverage against the resolved source routes.
   Require hosted parser contracts for any new route and update this review with
   PASS/FAIL/BLOCKED evidence. Do not silently select an unresolved route.

Item 1 bounded follow-up passed hosted run 35168707877: all nine main sources are
advertised Active Specifications in the official DCAT feed; all nine In Effect
specification rows are observed. Combo view metadata/three-row identity relation
and cross-brand Range Hood rows are retained in EPA_ROUTING_SOURCE_CONTRACT.md.
This closes the advertisement and alternate-view observation gaps, while exclusive
version, stacked/per-configuration routing and individual applicability remain open.

Item 2 bounded evidence collection passed hosted run 35169376748: declared eCFR
Title 16 version/Part 305 clauses, EPA laundry criteria and grouped special_type
observations are retained. The 11-family matrix and configuration boundaries are
in APPLICABILITY_EVIDENCE.md; exact SKU applicability and all decisions stay open.
Fixture integrity run 35169376791 verifies 99 references on Ubuntu.

Next bounded task: item 3, final G0 source-contract/fixture coverage closure and
explicit phase-specific deferrals. No compliance rule or Phase 1 code is
needed to collect these official source observations. Ask only if a semantic
choice becomes necessary to close a route; existing deferred decisions stay open.

## Later phase work; do not add it to today's completion claim

| Due phase | Work / decision dependencies |
|---|---|
| Phase 1 | Typed schemas, canonical SKU/provenance joins, run/evidence manifests, fixture CI including Python 3.11 compatibility (MASTER_PLAN §0), D04/D08/D11/D12 boundaries |
| Phase 2 | Complete refrigerator PDP/label/EPA collection; approved comparison, OCR corroboration, market/current-certification/wildcard semantics; full glyph, naturally degraded, corrected/wrong-model golden suite; D01–D04/D07/D09/D10 |
| Phases 3–4 | Full population collection and applicability/rule validation for the remaining product groups |
| Phases 5–7 | History, durable raw-evidence storage and operational recovery, publication gates; D05/D06/D12 |

The raw hosted artifacts expire after 14 days; compact projections and sanitized
text/coordinate fixtures cannot replay an original PDF. Durable retention design
is a later phase dependency, and expiry must be considered when rerunning a raw
evidence review. Historical failure records remain in docs/evidence; subsequent
success does not erase them.

Token handoff: use existing Terra medium guidance for this fixed checklist and
evidence maintenance; use Sol medium for the next new EPA source contract. Read
compact metadata and relevant diffs; reuse existing successful runtime evidence.
No dependency install or browser/OCR run is needed for the fixture-hash checkpoint.
Actions runtime LLM calls remain zero.
