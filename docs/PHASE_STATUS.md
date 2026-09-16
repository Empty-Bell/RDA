# Phase status

Phase 0: RUNNING — bounded refrigerator, dishwasher, washer and TV source reconnaissance PASSED on hosted Ubuntu.
Phases 1–7: NOT_STARTED.

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

Next bounded task: Range EPA-focused source-contract reconnaissance.
Other 7 families and remaining claim/quality semantics are not complete.
Do not advance to Phase 1 until full G0 is verified.

Follow-ups before locking runtime: freeze transitive Python dependencies and OCR model hashes;
replace older Node20 Actions pins with verified current releases (runner currently upgrades
them to Node24; first run succeeded with warnings). No downgrade flag should be enabled.

Token handoff: use Sol medium for the next exploratory source contract only; Terra medium
for repeated adapters after the contract is fixed. Read relevant docs and artifact fields,
not complete dependency logs or all source payloads. No LLM calls in Actions runtime.
