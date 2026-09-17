# Phase status

Phase 0 / G0: PASS — source reconnaissance contracts and hosted execution foundation accepted 2026-09-17. See G0_ACCEPTANCE_RECORD.md. This is not full per-SKU collection, certification matching or compliance PASS.
Phase 1 / G1: PASS — schema/config/manifest/CLI/report/fixture and quality CI accepted 2026-09-17.
Phase 2 / G2: RUNNING — observational refrigerator pilot (listing, one PDP/PDF, EPA brand snapshot).
Phases 3–7: NOT_STARTED.
No G2 gate is accepted yet; pilot collection success is not whole-SKU coverage or assessment PASS.
See G1_ACCEPTANCE_RECORD.md and docs/evidence/g1-acceptance-recon.json.
Hosted final run 35172241517, code dccaba9, attempt 1: Python 3.11.16 and 3.12.14
each passed 80 fixture tests (zero skips/errors/failures) and 15 static/build/
installed-CLI checks. Downloaded raw reports, wheel hashes and ZIP hashes verified.
Initial YAML parse failure 35172198096 was corrected before final acceptance.
G1 product/count/ID baseline is approved; remaining assessment/publication/history
policies stay OPEN at later gates. No live per-SKU compliance assessment is claimed.
Earlier G1 checkpoints: 35170618251 (28), 35171015637 (66), 35171608893 (80);
archived as foundation, typed-contract and population-report evidence.

Final hosted combined checkpoint 35169843199 tested code
6069bed296dde8bc418619af4888925fce30f118, attempt 1, job 105038925672:
214 tests (213 successful, one optional OpenCV test skipped) and 99 fixture
references verified. That OpenCV test executed in both existing cold 180-test
jobs. Prerequisite live source/runtime/routing/authority runs were independently
API-verified; see docs/evidence/g0-closure-recon.json. D01–D12 remain OPEN at their
due gates. Phase 0 stops here; next is G1 schemas/CLI/manifests/fixture CI.
The notes below retain the chronological progress and failure/success history.

Desktop User-Agent validation (commit 434f5af6b99d83e99306e3b51b61344a61f4b896):
- Source recon https://github.com/Empty-Bell/RDA/actions/runs/35102481369 — success
- Runtime probe https://github.com/Empty-Bell/RDA/actions/runs/35102481276 — success
- Installed Chromium OS/version retained; HeadlessChrome token replaced by Chrome.
- navigator.userAgent and observed pf_search request UA checked against configured UA.
- 20 contract/guardrail tests and live source checks passed on hosted runners.
- This is post-change success, not evidence that UA caused the earlier 403 or permanently resolved it.

Hosted evidence:
- Run: https://github.com/Empty-Bell/RDA/actions/runs/35100312790 (success)
- Commit: 8b786bac4ea15afa5b2a892815e6cbc80644d58a; attempt 1
- Job: 104807778999
- Artifact: phase0-probe-35100312790-1, ID 10448091149, 112790 bytes
- ZIP SHA256: ca1ff0ee9ba51477381f70fa4e4ceb9c903b850f9ba743a7cfead0472e21c4d7
- Artifact expiry: 2026-09-30
- Passed: cold install, 3 guardrail tests, disk budget, embedded PDF/image-only OCR,
  headless Chromium + Samsung pf_search observation, EPA catalog access, artifact upload.

Full G0 acceptance is NOT_EVALUATED. Initial probe is deliberately bounded to runtime
and a refrigerator source sample. No compliance decisions implemented.

Refrigerator source evidence:
- Run https://github.com/Empty-Bell/RDA/actions/runs/35101976503, success
- Commit 4c0193c06f921af4b38b8d895d78a953a838ff0e, attempt 1, job 104813390799
- API groups = rendered cards = Results text = 41; 75 unique exact SKUs
- 20 tests passed on hosted runner, including schema drift and missing/duplicate identity controls
- Exact sample PDP Specs/Support and live image-only EnergyGuide PDF verified
- PyMuPDF→RapidOCR 2x fallback; label RF29DB9900**, 700 kWh, 28.6 cu.ft. visually checked
- EPA p5st-her9 metadata/schema/sample verified; certification matching NOT_EVALUATED
- Artifact 10448527895, SHA256 35bd70c32cc77e398f507a3701bbc2d7c6cfbdc43449eef19eb552fa46c27d2c
- Partial 403 run 35101447985 preserved as access-health evidence, not missing product/certification

Dishwasher bounded source checks passed in run 35103320640 (commit ac7d3a8).
9 API groups = 9 rendered cards; 21 exact SKUs; sample DW90F89P0USRAA PDP/PDF
and q8py-6w3f EPA schema/sample verified. Fixture tests expanded from 20 to 28.
Final 28-test hosted dishwasher validation: run 35103625881, job 104819058726,
commit 629e3a6a21baa1a39f03e4bd61d0435640b30189 — success.
Mixed US/Canada PDF requires US-region OCR selection before automatic field parsing.
See DISHWASHER_SOURCE_CONTRACT.md and docs/evidence/dishwasher-source-recon.json.

Washer bounded reconnaissance PASS: run 35104751514, commit eb0689f9d392e310875afb8d1378f62fcc7f9ad7,
job 104822950139. 39 tests and five live source checks passed; all three family jobs success.
18 API groups = 18 rendered tile groups; 37 exact SKUs; combo WD90F53AVBUS and
front-load WF90F53ADSA5 sample PDP/PDF plus bghd-e2wd EPA schema/sample verified.
Partial embedded text missing kWh now triggers OCR; both label renders manually checked.
Run 35104431554 refrigerator pagination failed due to repeated group across offsets;
preserved as source-health failure, not corrected into PASS. Final snapshot passed.
See WASHER_SOURCE_CONTRACT.md and docs/evidence/washer-source-recon.json.

TV bounded source reconnaissance PASS: run 35105667331, job 104826096860,
commit 8af4267b3c8309dc70ec032afe2d2080fd4441bc; 47 tests and all four source checks passed.
All four family jobs in this final hosted run concluded success.
41 API groups = 41 rendered tile groups; 167 exact SKUs; sample MRN75R95HAFXZA
PDP/PDF and pd96-rr3d EPA schema/sample verified. Preserve power W versus annual
kWh and product $62 versus cost range $32–$155; identity suffix matching is open.
See TV_SOURCE_CONTRACT.md and docs/evidence/tv-source-recon.json.

Range EPA-focused reconnaissance PASS: run 35106676958, range job 104829597830.
54 tests and four source checks passed; 19 API groups = 19 rendered tile groups,
All five family jobs in the final run concluded success (commit 7ca2c669b7c194da59451d32fcbc87fd4a3d1dd8).
58 exact SKUs; sample NSE80H63XRAA Specs/Support and m6gi-ng33 schema/sample verified.
Fuel/product-type applicability and Samsung certification matching remain open.
EnergyGuide PDF probe is OUT_OF_RECON_SCOPE under the master plan's EPA-only scope.
See RANGE_SOURCE_CONTRACT.md and docs/evidence/range-source-recon.json.

Cooktop EPA-focused reconnaissance PASS: run 35107565285, job 104832622093,
commit d6fb2a490e363f24c00df29d9e05f648d4b18f1f. 62 tests and five source checks passed.
All six family jobs in this final hosted run concluded success.
9 API groups = 9 rendered tile groups; 20 exact SKUs; gas NA30N6555TS/AA and
radiant electric NZ30K7570RS/AA sample Specs/Support plus m6gi-ng33 schema/sample
verified. EnergyGuide is OUT_OF_RECON_SCOPE under EPA-only scope. No EPA SKU lookup.
See COOKTOP_SOURCE_CONTRACT.md and SOURCE_COVERAGE.md for actual coverage limits.

Clothes Dryer EPA-focused reconnaissance PASS: run 35109208255, job 104838211794,
commit bb87f1aa2530a56d4327e8a88d245f76590dffa8. 71 tests and five source checks passed;
all seven product group jobs concluded success. 19 API groups = 19 rendered groups,
54 exact SKUs; combo WD90F53AVBUS and standalone DV90F53AESA3 PDP plus t9u7-4d2j
metadata/schema/sample verified. Mixed-case Energy Star Certification now retained.
103 kWh combo washer label is not dryer energy; annual dryer energy projection remains
UNKNOWN where no verified spec exists. Earlier refrigerator duplicate pagination failure
run 35108542847 preserved; final source snapshot passed. See DRYER_SOURCE_CONTRACT.md.

Ventilating Hood EPA-focused reconnaissance PASS: run 35110234760, job 104841727946,
commit a5b4494b39fed2992aa7503d6e4d673a749e06d5. 79 tests and four hood source checks
passed; all eight family jobs succeeded. 6 API groups = 6 rendered groups, 16 exact
SKUs; NK30CB700WCGAA sample PDP plus 8dv7-nngq metadata/three generic rows verified.
Raw CFM range, power W, noise dBA/sones and venting type remain separate; bathroom
fan sample is not hood certification matching. EnergyGuide is OUT_OF_RECON_SCOPE.
See HOOD_SOURCE_CONTRACT.md and docs/evidence/hood-source-recon.json.

Monitor / Display EPA-focused reconnaissance PASS: run 35111109416, job 104844741738,
commit eb170dfcf1f4ffd9b4167b916e469cee2023935d. 88 tests and four monitor source checks
passed; all nine family jobs succeeded. 56 API groups = 56 rendered groups, 76 exact
SKUs; LS40H850TANXZA sample PDP plus qbg3-d468 metadata/three generic rows verified.
Maximum consumption 340 W remains separate from Thunderbolt output 140/15 W;
class size, active dimensions and resolution retained separately. Generic signage row
without annual monitor energy is not a Samsung match or zero-energy observation.
EnergyGuide is OUT_OF_RECON_SCOPE. See MONITOR_SOURCE_CONTRACT.md and evidence.

Computer EPA-focused reconnaissance PASS: run 35114575198, commit
deabaff76e980ba33c97e54a3fd4ad31ba60532f; Galaxy Book job 104856607424,
Chromebook job 104856607323. 103 tests and four live checks per Computer source leg
passed; all 11 source jobs for 10 product groups succeeded. Separately linked Galaxy
Book 11 groups/23 SKUs + Chromebook 1 group/1 SKU yield a verified 24-SKU union.
NP960UJH-XG7US and XE550XGA-KC1US sample PDPs verified using selected SKU / visible
purchase control and exact Specs-only array. Battery Wh, adapter W and TEC kWh remain
distinct; Support is NOT_EVALUATED, metadata count null; EnergyGuide OUT_OF_RECON_SCOPE.
Earlier lazy-summary/Specs contract failures and implementation pagination regression
are preserved in computer-source-failure-history.json; stale failed run 35113871784
was cancelled after evidence preservation. Final regression recovered all source jobs.
See COMPUTER_SOURCE_CONTRACT.md and docs/evidence/computer-source-recon.json.

Tablet EPA-focused reconnaissance PASS: run 35159081725, commit
76d0e271c58a9a02f88efaa3447101168b6dcf40, job 105005374161. 115 tests and all
12 source jobs for 11 product groups succeeded. Tablet 11 API/rendered groups,
50 exact SKUs; SM-X930NZAAXAR sample verified through selected configuration,
visible Continue SKU and Specs-only array. Preserve 11600 mAh separately from
Wh/annual energy and Up to 23 playback hours; EPA rxdj-2c88 metadata + 3 generic
rows is not candidate matching. Initial Chromebook timeout and final recovery
are preserved without relaxing identity gates. See TABLET_SOURCE_CONTRACT.md,
SOURCE_COVERAGE.md and docs/evidence/tablet-source-recon.json.

Independent public claim/identity bounded discovery PASS: run 35160456564,
commit 8b1ee4d0a798179a64486b782f0c0709225597ea. 126 tests and all 12 source jobs
succeeded. Raw PLP flags, card candidates, PDP headings/exact Product JSON-LD,
direct modelCode-identified structured fields, spec claims and page logo candidates
are separately retained. Initial Computer loading failure is preserved; one bounded
reload retains failed attempts without relaxing identity. No claim truth, normalized
commerce status, certification or consistency decision was made.
See PUBLIC_CLAIM_IDENTITY_CONTRACT.md and public-claim-identity-recon.json.

Current-product badge attribution / inline flag contract PASS: run 35162114501,
commit a39c9e3914c13a7554ab1954c3edd18827b3fea3. All 12 source jobs succeeded
with 143 tests. Unique primary gallery/configurator surfaces, sole exact Product
JSON-LD and existing PDP identity gates corroborate attributed logo candidates.
Nested product projections retain JSON paths and explicit SKU scope; unrelated
branches cannot inherit the target. Trade-in/navigation/pricing are explicitly
outside product-field scope; initial trade-in truncation remains in fixtures.
All primary samples have one exact raw energyStarFlag from public NEXT_DATA
props.pageProps.productData.products. Strict array-only extraction eliminates unrelated
page traversal/truncation; missing/duplicate target records fail extraction. Actual
Computer Y / TV N fixtures preserve raw flags, without taking the first array row.
See CLAIM_ATTRIBUTION_SOURCE_CONTRACT.md and claim-attribution-recon.json.
Unobserved flags and unsupported surfaces stay NOT_EVALUATED; no EPA/consistency
rule or normalized commerce mapping was introduced.

EnergyGuide raw field/coordinate reconnaissance PASS: run 35163198471, commit
9f577eeb38b95cb49e49be6d1f453a1b8709ff82. All 12 source jobs succeeded with 154
tests. Five observed label fixtures retain original PDF hashes, independent embedded
text/OCR detections, PDF-space coordinates and numeric/caption proposals. US
dishwasher 225 is geometrically separated from Canadian 200/307 reference values;
text-order uncertainty remains preserved. No canonical field selection, wildcard
correction, label/SKU matching or compliance decision was introduced. Initial failing
mixed-order tests and corrected runs remain in the failure history. See
ENERGYGUIDE_FIELD_SOURCE_CONTRACT.md and energyguide-field-recon.json.

EnergyGuide degradation/model-like ROI reconnaissance PASS: run 35164831308,
commit 250dee4665ae9d3bf8c4c0f4142e7f398c74375d. All 12 source jobs succeeded
with 165 tests, including the actual repeated-star PNG preprocessing fixture.
Five original labels yield 36/72-DPI controlled page degradations and separate 3x
color/grayscale-Otsu model-like ROI evidence. Source/PNG/OCR hashes and PDF-space
coordinates retain provenance. Observed digit substitution, model/caption loss,
wildcard-count disagreement and part-number confusion remain uncorrected.
See ENERGYGUIDE_QUALITY_CONTRACT.md, energyguide-quality-recon.json and the fixture
manifest. This is a controlled degradation corpus, not naturally degraded PDF
coverage, canonical model identity or the complete approved OCR acceptance matrix.

EPA query/catalog/type/update bounded extraction PASS: run 35165687365, commit
6c72dfd3cd5cfbd409456d15b82580619274292a. Nine distinct dataset jobs passed 12
query tests; full source regression run 35165687343 passed 177 tests and all 12
source legs. Declared literal Samsung-brand scans preserve terminal pages, before/
after counts and unchanged metadata; errors and malformed responses are rejected.
Normal fan 0-row query, missing UPC, non-US market strings, raw types and repeated
wildcards stay observations. Equality probes seed from EPA rows, not retail SKUs.
Configured datasets are advertised in the official-domain catalog; search results
include unrelated entries, so sole current version/certification remain unknown.
See EPA_QUERY_SOURCE_CONTRACT.md, epa-query-recon.json and the actual fixture manifest.
No current-certification, applicability, matching or compliance rule was introduced.

Hosted application runtime freeze / controlled recovery PASS: code
bf6078724ebda11384860219be82f63bfc82b4de. Two independent cold jobs in run
35166865310 passed 180 tests, pinned resource integrity, expected isolated model
corruption rejection/recovery and PDF/CPU-OCR/Chromium/Samsung/EPA live probes.
Full source 35166865304 passed all 12 legs; EPA 35166865352 passed all nine jobs;
separate runner probe 35166865316 passed. Python 3.12.14, hashed transitive/build
locks, three ONNX/configuration hashes and Node24 Actions are explicit. Existing
bad bytes fail before collection; bootstrap failures retain stage/exit-code evidence.
Original runtime/model resources are untouched by controlled-copy recovery. The
initial directory orchestration failure is confirmed and preserved. See
RUNTIME_FREEZE_CONTRACT.md and runtime-freeze-recon.json. Image/system libraries
remain GitHub-managed; arbitrary WAF/network recovery and future reachability are
not implied by this PASS.

Consolidated G0 evidence review and phase-specific gap inventory are recorded in
G0_REVIEW.md. Fixture manifest capture/committed byte distinctions and ambiguous
refrigerator paths are corrected; a dedicated hosted integrity checkpoint is added.
No fixture facts, raw ZIP/PDF hashes, decisions or compliance rules were changed.
Hosted integrity review PASS: run 35167790999, commit
3e4d5ea3c5ac0947c99e955ef3bac3054dac5302, attempt 1, job 105032662559.
All 92 fixture references match actual Ubuntu checkout bytes. Archive/report
hashes and expiry are recorded in docs/evidence/g0-integrity-review.json.
Local changed-byte, missing-file and traversal checks reject invalid evidence.
Official EPA source-routing bounded PASS: run 35168707877, code
cfac061e4cb81314b031c60b1febbe905b6c75cd, attempt 1, job 105035493022;
16 dedicated routing and 12 query-boundary tests passed. Official DCAT advertisement
and specification status, combo-view/parent-filtered three-row identity relation,
separate washer/dryer energy fields and actual fan unit_type/Range Hood rows are
preserved. Two failed probes and corrections remain in the failure history.
See EPA_ROUTING_SOURCE_CONTRACT.md and docs/evidence/epa-routing-recon.json.
No production route, matching, applicability or compliance policy was changed.
Official applicability evidence bounded PASS: run 35169376748, code
b6e6f13c76041d8aa0034d04243060646a0abb65, attempt 1, job 105037485756;
12 authority contract tests passed. Actual dated eCFR XML yields nine required
sections; source dates and before/after stability are retained. EPA criteria and
literal Samsung special_type queries expose combo/center/unspecified distinctions.
Independent fixture run 35169376791 passed 99 references on Ubuntu. No applicability
or compliance policy was activated. See APPLICABILITY_EVIDENCE.md and
docs/evidence/applicability-recon.json. Remaining milestone gates: MILESTONES.md.
Final G0 source-contract/fixture coverage closure is now accepted in
G0_ACCEPTANCE_RECORD.md. All family discovery and bounded common
claim/quality/runtime/authority probes are complete within reconnaissance scope.
See G0_ACCEPTANCE_CHECKLIST.md for intermediate artifacts and verification gates.
G0 is verified for Phase 0 scope; Phase 1 implementation remains NOT_STARTED.

Application runtime locking is now hosted-verified. Future updates require reviewed
lock/model/Actions changes and cold plus full-source regression. Do not enable Node
downgrade flags or auto-refresh expected model hashes.

Token handoff: reuse the existing model guidance: Terra medium for the next bounded
evidence/checklist maintenance; Sol medium for the next EPA source-routing contract.
Read relevant docs and artifact fields,
not complete dependency logs or all source payloads. No LLM calls in Actions runtime.
