# Phase 0 / G0 acceptance — PASS, 2026-09-17

**Accepted scope: source reconnaissance contracts and GitHub-hosted execution
foundation.** This is the MASTER_PLAN Phase 0 gate, not full per-SKU collection,
certification matching, approved applicability policy or product compliance PASS.
Phases 1–7 remain NOT_STARTED. D01–D12 remain OPEN at their implementation gates.

The final [combined checkpoint](https://github.com/Empty-Bell/RDA/actions/runs/35169843199)
tested code `6069bed296dde8bc418619af4888925fce30f118`, attempt 1,
job 105038925672 on standard ubuntu-24.04 x64. It replayed **214 tests: 213 executed
successfully, one optional OpenCV test skipped**, with zero failures/errors, and
verified **99 manifest references** against actual checkout bytes. The skipped
ROI binarization test was executed in the existing locked-bootstrap 180-test suite
in both cold jobs; this lightweight checkpoint does not replace runtime/OCR probes.

The checkpoint report deliberately leaves `phase_gate: NOT_EVALUATED`. This
acceptance record assigns the reviewed gate after the source matrix, prior live
runtime/source evidence, parser boundaries and explicit deferrals below are
reconciled. A parser never promotes its own product or phase assessment.

## Requirement-to-evidence closure

| Phase 0 requirement | Verified evidence / contract | Result |
|---|---|---|
| All 11 product groups, current PLP endpoint and pagination/count grain | SAMSUNG_SOURCE_CONTRACTS.md and all family contracts; SOURCE_COVERAGE.md; [12 live source legs](https://github.com/Empty-Bell/RDA/actions/runs/35166865304) | PASS for dated listing discovery |
| Current structured PDP flow and exact identity | Same live source regression; family/PUBLIC_CLAIM_IDENTITY/CLAIM_ATTRIBUTION contracts; selected-config + Specs endpoint for computers/tablets | PASS for representative samples; unused Support stays unobserved |
| Current EnergyGuide provenance, download and field observations | Five actual label samples, field/quality manifests, prior live regression; ENERGYGUIDE_FIELD_SOURCE_CONTRACT.md / ENERGYGUIDE_QUALITY_CONTRACT.md | PASS for reconnaissance; no canonical model/annual-energy selection |
| Official EPA source identification and schema/query boundaries | Nine main schemas, declared Samsung scans, active DCAT/specification status; [routing](https://github.com/Empty-Bell/RDA/actions/runs/35168707877), [EPA regression](https://github.com/Empty-Bell/RDA/actions/runs/35166865352) | PASS for observed source scope; no current-model matching |
| Program/family applicability provenance and unknown boundaries | APPLICABILITY_EVIDENCE.md, [official dated authority probe](https://github.com/Empty-Bell/RDA/actions/runs/35169376748); XML §§305.2/3/9/13–16/25/27 and laundry criteria/type observations | PASS for source facts; individual classifications deferred |
| Hosted cold-start PDF/OCR/browser/access foundation | [Two independent cold jobs](https://github.com/Empty-Bell/RDA/actions/runs/35166865310), [separate probe](https://github.com/Empty-Bell/RDA/actions/runs/35166865316); GITHUB_HOSTED_RUNNER_CONTRACT.md / RUNTIME_FREEZE_CONTRACT.md | PASS; managed image and future reachability remain external inputs |
| Sanitized fixtures, contract replay and preserved errors | Final combined checkpoint and fixture manifests; prior failure-history records retained | PASS for reviewed parser contracts |
| Open questions and downstream scope are explicit | DECISIONS.md, deferrals below, MILESTONES.md | PASS for handoff documentation; no semantic approval |

The seven prerequisite hosted run conclusions/commits/attempts were independently
read from GitHub API during this review. The existing live evidence is reused;
the final checkpoint performs no new live source collection or package install.
Code, job, artifact/report SHA, raw expiry and reviewed scope are recorded in
docs/evidence/g0-closure-recon.json. Failures were not deleted or reclassified.

## Fixture category coverage

| G0 category | Contract replay evidence |
|---|---|
| Normal responses | Actual per-family PLP/PDP/EPA fixture tests, five EnergyGuide label fixtures, routing/authority fixtures |
| Valid empty observation | g0_closure_test valid-empty listing; EPA complete-zero and actual empty fan-brand query tests; no compliance/absence inference |
| Next/last page and incomplete scan | Family pagination tests; refrigerator full pagination/missing terminal/count drift; EPA explicit empty terminal, overlap/truncation/source-change tests |
| Missing required fields | Shared pf pagination/variant/null list checks; PDP exact SKU/Specs/Support or selected-config gates; per-dataset schema and authority date/section tests |
| Duplicate variant/identity | Shared duplicate SKU/representative removal/cross-page group checks; PDP duplicate identity and selected configuration tests; EPA source-row overlap checks |
| Errors and unsupported shapes | Source error object/negative/boolean count, HTTP 200 HTML non-PDF, EPA non-200/HTML/error object/malformed JSON, malformed XML/DTD/entity and authority drift tests |

Fault mutations are explicitly synthetic derivatives of sanitized observed fixtures;
they are not claims that those errors occurred in Samsung production. Shared parser
boundaries apply to the source legs using that parser. The complete later OCR
glyph/correction/wrong-model corpus is a G2 requirement, not claimed here.

## Why remaining unknowns do not approve rules or block source discovery

All eleven source rows have observed endpoints, representative identity, declared
EPA source/schema and official program references. No unobserved dataset is passed
as an active route. Combo alternate-view identity relations and fan Range Hood
records are observed; stacked/paired/per-configuration policies are not selected.
Gas cooking exclusions, tablet cellular-voice exclusions and zero fan-brand rows
are preserved as scoped source facts, without a legal N/A or certification verdict.

The formerly open Phase 0 tasks were official source advertisement, alternate-view
observations and applicability provenance; these now have hosted evidence.
Exclusive-version/model-certification currency, wildcard/UPC/US-market matching
and SKU classification are assessment policies for G2/G4. They remain disabled
until D09 is decided; calling G0 PASS neither resolves D09 nor relaxes its gate.
D08's observed count grain is documented by family; canonical namespaces/joins
still require the G1 data contract. Deferred policies cannot silently become defaults.

| Due gate | Required handoff |
|---|---|
| G1 | Canonical SKU/source provenance, null/unknown/error distinctions, run/evidence schema, aggregation grain, retry/storage identities; D04/D08/D11/D12; Python 3.11 fixture CI |
| G2 | D01–D04/D07/D09/D10 decision tables; approved comparison/test basis/tolerance, OCR corroboration, current/market/pattern semantics, pipeline versus product failure, complete refrigerator coverage and golden OCR suite |
| G3/G4 | Family-specific applicability and measurement mapping, full populations, stacked/paired/configuration facts and approved identity policy before evaluation |
| G5–G7 | D05/D06/D12, history/long-term raw retention/recovery/publication policy and complete hosted operation/Pages gates |

Raw artifacts currently expire after 14 days. Compact projections do not replace
original PDFs for rerender/OCR; later replay requires available raw inputs or new
captured evidence. eCFR's declared up-to-date-as-of date is 2026-09-15. No source
fact is presented as perpetual availability or a final legal conclusion.

Phase 0 stops here. **Next: G1 schemas, CLI skeleton, manifests and fixture CI.**
No decision engine or deployment was implemented. Collection/test runtime LLM calls
remain zero; this closure avoids repeating unchanged heavy runtime/source probes.
