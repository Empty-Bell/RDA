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
EnergyGuide retrieval verified 162/167 PDFs and exposed five failing Samsung
URLs. The collector now checks HTTP status, PDF bytes, and the final HTTPS
Samsung URL independently of a potentially incorrect Content-Type header, and
records response details on failure. The GitHub-hosted label/EPA capture has
been restarted against the verified PDP artifact; candidate comparison remains
pending.

Recommended model for fixed-schema collection review: GPT-5.6 Luna low; use
GPT-5.6 Terra medium only if a new TV-specific source adapter or comparison rule
is required. Collection/runtime itself uses no LLM.
