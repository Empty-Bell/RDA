# Television source reconnaissance

Status: bounded TV source reconnaissance PASS on hosted Ubuntu (run 35105667331).
Phase 0 remains RUNNING; certification matching/compliance NOT_EVALUATED.

Official discovery:
- Samsung listing: https://www.samsung.com/us/televisions-home-theater/tvs/all-tvs/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-televisions
- EPA metadata: https://data.energystar.gov/api/views/pd96-rr3d.json
- EPA sample: https://data.energystar.gov/resource/pd96-rr3d.json?$limit=3

Observed EPA metadata identifies ENERGY STAR Certified Televisions, pd96-rr3d.
Separate reported_annual_energy_consumption_kwh (annual energy),
power_consumption_in_on_mode_watts (certification average on-mode power),
reported_on_mode_power_per_the_federal_test_procedure_watts (federal test power),
diagonal_viewable_screen_size_inches and date_qualified (displayed Date Certified).
Power W cannot substitute for annual kWh. Test basis and operating mode must remain
attached to values; multiple power fields are not synonyms.

Samsung category/group/request pagination and PDP spec names must come from the
actual page/network. Screen-size siblings retain exact SKU provenance. Current API
groups must reconcile with terminal pages and distinct rendered card groups.
Sample Specs/Support selects exact modelCode. Preserve original EnergyGuide before
PyMuPDF/OCR extraction. OCR fallback checks empty, short and missing numeric kWh text;
this is extraction health, not a complete field-quality or compliance gate.

Runtime: standard cold ubuntu-24.04 x64, installed-version desktop Chromium UA,
bounded retries, no LLM. All acceptance requires real hosted Actions evidence.

## First hosted source observations

Run https://github.com/Empty-Bell/RDA/actions/runs/35105336825, commit 246a657,
TV job 104824957815 source checks PASS. Listing redirects to /us/tvs/all-tvs/.
POST pf_search category_code `04010000`, offsets 0/21, request counts 21/24,
returned rows 21/20, terminal total 41 groups and 167 unique exact SKUs.
41 distinct rendered card groups reconcile with the observed API total. Unlike the
appliance samples, the first TV request uses 21 rather than 14; preserve observed
request pagination. Counts are fixture assertions, never fixed production targets.

Target MRN75R95HAFXZA Micro RGB 75-inch PDP uses observed bridge-data group_id 585741.
Exact Specs: Screen Size `75"`; Power Consumption (Typical) `208 W`, (Max) `370 W`,
(Stand-by) `0.5 W`. No annual kWh or ENERGY STAR spec claim observed in this sample.
Missing observed claim remains UNKNOWN, not a false/no-certification determination.
Screen size is independent screen-size data, not appliance capacity. Never derive
annual electricity from Typical W without an approved operating-hours/test contract.
Exact Support provides EnergyGuide PDF even though no rendered anchor was found.

PDF https://images.samsung.com/is/content/samsung/p6pim/us/mrn75r95hafxza/energyguide/us-energyguide-mrn75r95hafxza-551652054.pdf
HTTP 200/application/pdf, 67874 bytes; SHA256
`791734f108ea20ad2366e79f7a7f0ba2e85020da6a6631c0bc60d2cfe8e174ed`.
Empty embedded text; 2x RapidOCR fallback. Visually checked label model MRN75R95HAF,
estimated yearly energy cost $62, similar-model range $32–$155 (69.5 inches or greater),
390 kWh annual electricity, 16 cents/kWh and 5 hours/day. OCR emits $155 before $62:
reading order does not define which amount is the product's cost. Preserve coordinates
for future field selection. Label model lacks the PDP's XZA suffix; exact identity
matching remains unapproved. Do not strip suffixes merely to obtain a match.

First artifact 10450590021 (236857 bytes), ZIP SHA256
`a3ad0c706ec17b7503663c79e3b0069bc0a611c1a6632a0d796d92933f3693e4`.
Raw PDF/render expires 2026-09-30. Full per-SKU PDP coverage, label identity/field
quality, test-basis comparison and EPA candidate/currency matching remain open.

## Final hosted acceptance

https://github.com/Empty-Bell/RDA/actions/runs/35105667331
Commit 8af4267b3c8309dc70ec032afe2d2080fd4441bc, TV job 104826096860.
47 tests, all four TV source checks and artifact upload PASS on cold hosted Ubuntu.
Final TV artifact 10449812938 (236899 bytes), ZIP SHA256
`094b9a290acb3b2f6b40694088c5783cf46536d2ebf88f51e5893b01cae1f7be`.
Source observations/label manual check: docs/evidence/tv-source-recon.json.
Per-fixture hashes/source run IDs: docs/evidence/tv-fixture-manifest.json.
Raw evidence expires 2026-09-30. This is one sample PDP, not all 167 SKU coverage.

Next bounded source group: Range (EPA-focused). Continue with source discovery;
do not apply appliance annual-energy or FTC PDF obligations to EPA-only groups
without an approved rule contract. Existing Sol medium exploratory model guidance
applies; runtime has no LLM calls.

## G3 handoff after Washer

The automated hosted chain refreshes source discovery, collects every exact-SKU
PDP (167 in the captured sample), then retrieves Support-declared EnergyGuide
PDFs and captures the full EPA TV cohort in parallel. If those sources pass,
the chain observes raw text/layout/OCR and generates a same-run source-candidate
comparison without grading. PLP claim flags, exact Specs/Support facts, and PDP
claim evidence stay attached to each SKU. Source recon passed; the first PDP
collection failed and is now being moved to failed-SKU-only parallel recovery.

Apply the approved common rules: comparable annual-kWh disagreement is MEDIUM;
missing PDP annual kWh while label and EPA values agree is LOW; EPA Current Model
Index absence plus any PLP logo, PDP logo, or spec certification claim is HIGH.
If EPA is absent and all three publication points are absent, there is no ENERGY
STAR finding and the SKU displays PASS. TV typical/max/standby W remains a separate
quantity from annual kWh; never derive one from the other. The sample PDP had no
annual kWh field, so this LOW rule may apply if full-population sources confirm
the same gap. PDF/model identity and field selection remain candidate evidence
until the comparison artifact exposes them for review.

The initial full-population collection failed after 40m33s with 47 exact PDPs
verified and 120 failed. The first recovery took about six minutes. Saved
evidence showed 119 PDPs had a valid exact-SKU URL and exact-SKU Specs/Support
bridge, but each also had anonymous Product JSON-LD shells. Identity validation
now ignores only those unidentified shells while continuing to reject any
conflicting identified SKU. `QN100QN80FFXZA` once redirected to a
`QN115QN90FFXZA` PDP; its retry passed, and the assembled collection has 167/167
verified. Initial collection now runs in eight shards. EPA capture passed.
EnergyGuide retrieval verified 162/167 actual PDFs and exposed five Samsung
URLs returning 70–79 KB bodies that begin `<## NASC` despite claiming
`application/pdf`. These are not accepted as PDF evidence. The collector records
the response prefix, requests identity encoding, and fetches up to eight URLs
in parallel. EPA capture passed.

The five responses decode to `NASC A DRM FILE - VER1.00`. Under the existing
MASTER_PLAN §12 readability rule, each is recorded as `NOT_ACCESSIBLE` and a
HIGH `ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE`. They do not block OCR and
same-run candidate comparison for the 162 byte-verified PDFs. The comparison
must preserve these five explicit HIGH candidates and leave values unavailable
where no readable label exists; it must not infer label values.

TV quantity comparisons must remain unit-compatible: compare a model-matched
EnergyGuide annual kWh candidate to an exact Current EPA annual kWh candidate;
compare PDP `Power Consumption (Typical)` W separately to EPA on-mode and
federal-test W. Never compare PDP W to annual kWh. A unique label/EPA annual-kWh
difference after both exact/prefix model links and US-market scope are verified
is a MEDIUM candidate. PDP currently publishes no annual-kWh field for this
cohort, so absence alone is not a missing-value verdict in this family.

The corrected MNA-excluded collection passed hosted validation in run
35703343706 at commit 011ee1f: 165/165 exact-SKU PDPs verified. The new
population evidence retains the source count and explicitly records excluded
model prefixes and exact SKUs. Business scope excludes every exact TV SKU whose
model code begins `MNA`; the two baseline models were `MNA101MS1BCXZA` and
`MNA89MS1BACXZA`.

Downstream label/EPA capture run 35704036734 passed: 165 documents declared,
160 valid readable PDFs, five NASCA DRM labels and a successful EPA Current
capture. Corrected comparison run 35704080904 passed on hosted Ubuntu with 165
rows and no MNA SKUs. All 160 readable labels yielded one annual-kWh candidate
and matched an exact model pattern. Five remain NOT_ACCESSIBLE / HIGH.
EPA Current had exact US model-pattern matches for 35 SKUs, and all 35
label/EPA annual-kWh pairs differed, yielding 35 MEDIUM candidates. The other
130 had no exact EPA model match; 59 showed only 5–8-character near-prefix
diagnostics, which are not treated as matches or findings.

PDP typical power (W) was compared separately with EPA on-mode power (W): 20
rows differ, 138 have no exact EPA on-mode record, and seven PDPs lack a typical-W
candidate. These remain source-comparison candidates and are not emitted as
severity findings. The run's PASS means collection/comparison completed; no final
product grading was performed. Full row evidence is in the
[comparison workflow artifact](https://github.com/Empty-Bell/RDA/actions/runs/35704080904).

The 35 annual-energy differences are all label-higher-than-EPA (median +17.5%).
They share exact label/EPA model strings and a single OCR annual-kWh candidate,
so the uniform direction is unlikely to be caused by OCR/model mismatch alone.
Do not treat the size of this delta as proof of a publication error yet. ENERGY
STAR [V9.1](https://www.energystar.gov/sites/default/files/2024-08/ENERGY%20STAR%20Version%209.1%20Televisions%20Specification.pdf)
says its certified AEC uses the DOE Federal Test Procedure (Appendix H) and that
DOE represented values require separate testing under [10 CFR
429.25](https://www.ecfr.gov/current/title-10/section-429.25). That rule derives
represented annual energy from statistically represented power values. FTC
television representations use procedures in 10 CFR Parts 429 and 430 ([FTC 16
CFR 305.8](https://www.ecfr.gov/current/title-16/section-305.8)). Thus the
EnergyGuide may show DOE's represented rating while EPA's Current field reflects
a certified test AEC. This is a strong explanation for systematic positive
differences, but per-model DOE sample/represented values are not in the captured
EPA artifact, so it remains a hypothesis pending field-level confirmation. The
35 MEDIUM rows remain candidates, not confirmed product errors.

The 35 annual-energy differences are all label-higher-than-EPA (median +17.5%).
They share exact label/EPA model strings and a single OCR annual-kWh candidate,
so the uniform direction is unlikely to be caused by OCR/model mismatch alone.
Do not treat the size of this delta as proof of a publication error yet. ENERGY
STAR [V9.1](https://www.energystar.gov/sites/default/files/2024-08/ENERGY%20STAR%20Version%209.1%20Televisions%20Specification.pdf)
says its certified AEC uses the DOE Federal Test Procedure (Appendix H)
and that DOE represented values require separate testing under [10 CFR
429.25](https://www.ecfr.gov/current/title-10/section-429.25).
That rule derives represented annual energy from statistically represented power
values. FTC television representations use procedures in 10 CFR Parts 429 and
430 ([FTC 16 CFR 305.8](https://www.ecfr.gov/current/title-16/section-305.8)).
Thus the EnergyGuide may show DOE's represented rating while EPA's Current
field reflects a certified test AEC. This is a strong explanation for systematic
positive differences, but per-model DOE sample/represented values are not in the
captured EPA artifact, so it remains a hypothesis pending a field-level contract
check. The existing 35 MEDIUM rows remain candidates, not confirmed product
errors.

Recommended model for fixed-schema collection review: GPT-5.6 Luna low; use
GPT-5.6 Terra medium only if a new TV-specific source adapter or comparison rule
is required. Collection/runtime itself uses no LLM.
