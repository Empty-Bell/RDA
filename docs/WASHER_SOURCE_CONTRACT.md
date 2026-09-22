# Clothes Washer source reconnaissance

## Current continuation status (2026-09-22)

The source refresh run 35680095563 was followed by a complete exact-SKU PDP
identity collection in run 35681575057, a parallel Support-PDF/EPA capture in
run 35682498558, and hash-bound embedded-text/OCR observation in run 35682719846.
All three workflows passed on GitHub-hosted Ubuntu. Current capture details and
per-SKU document coverage are preserved in their run artifacts and summaries.
The scripts do not match label model text to PDP/EPA models, select a yearly-energy
value, route combo products, or assess compliance. Next is the raw candidate review
table, then a source-backed determination of washer versus all-in-one combo EPA/label
applicability. Any previous "next product family" language below is historical and
does not supersede this active Washer checkpoint.

## Same-run PDP / EnergyGuide / EPA comparison (2026-09-22)

Comparison workflow [35685571247](https://github.com/Empty-Bell/RDA/actions/runs/35685571247)
passed after the exact-SKU PDP collection, Support PDF retrieval, OCR observation,
and raw candidate review were linked by their source run IDs. Scope is all 37 Washer
SKUs. The output retains source values and model patterns without selecting a final
assessment or severity. EPA annual-energy candidate values are drawn only from a
matching current model row whose `markets` field explicitly lists the US.

Results: 22 SKUs have the same single annual kWh value in PDP, label, and EPA; 2
show differing values; 13 lack at least one PDP value or EPA model row. All 37 have
an exact PDP identity and at least one positional EnergyGuide model-pattern match.

The two value differences are the Laundry Center models `WH46DBH500EVA3` and
`WH46DBH500GVA3`: PDP lists 103 kWh/year; each Support label and its corresponding
EPA current row list 95 kWh/year. EPA rows classify both as Front Load / Laundry
Center, date qualified 2023-11-21. Treat these as unresolved source conflicts; do
not decide which number is correct or assign severity here.

Eight SKUs have no matching model row in the captured current EPA Samsung set:
`WA40A3005AW/A4`, `WA41A3000AW/A4`, `WA44A3205AW/A4`, `WA45T3200AW/A4`,
`WA46CG3505AVA4`, `WA46CG3505AWA4`, `WA47CG3500AVA4`, `WA47CG3500AWA4`. Seven of
these have a label value of 240 kWh/year and no PDP yearly-energy candidate; the
remaining `WA44A3205AW/A4` has 240 in both PDP and label. Five further SKUs have
label and EPA values that agree but no PDP annual-energy candidate:
`WA54CG7105AVUS`, `WA54CG7105AWUS` (120); `WF90F53ADSA5`, `WF90F53ADYA5` (103);
and `WW25FG6B34BEA2` (90). These source-coverage gaps are not yet assigned a
severity.

Next: review the two Laundry Center PDP fields against the underlying page facts,
and inspect the captured EPA model list for the eight no-row SKUs before enabling
washer assessment. Recommended model: Luna low for this evidence review; Sol
medium only if the evidence forces a new policy decision.

## Follow-up diagnostic (2026-09-22)

EPA candidate diagnostics reran on the same captured artifacts in
[workflow 35686761880](https://github.com/Empty-Bell/RDA/actions/runs/35686761880),
commit `40bc389`; no OCR or source recapture was needed. All eight previously
unmatched SKUs still have no EPA row after punctuation-only normalization. The
66-row Samsung cohort also contains no row sharing at least five initial
alphanumeric characters with any of those eight SKUs after punctuation removal.
This confirms absence from the captured current cohort under both exact pattern
matching and the bounded near-candidate check, without inferring a compliance
severity.

For `WH46DBH500EVA3` and `WH46DBH500GVA3`, exact-SKU PDP bridge evidence gives
`Energy Guide Label` = 103 kWh/year. Each PDP's Support-declared label prints the
corresponding wildcard model pattern and 95 kWh/year; each matching EPA row also
gives 95 kWh/year, Front Load / Laundry Center, qualified 2023-11-21. The current
Samsung pages confirm the two exact product IDs and distinguish the electric and
gas dryer variants ([EVA3](https://www.samsung.com/us/laundry/washer-and-dryer-sets/stacked-washer-and-dryer-bespoke-4-6-cu-ft-ai-laundry-hub-large-capacity-single-unit-washer-with-flex-auto-dispense-system-and-7-6-cu-ft-electric-dryer-in-brushed-black-sku-wh46dbh500eva3/),
[GVA3](https://www.samsung.com/us/laundry/washer-and-dryer-sets/stacked-washer-and-dryer-bespoke-4-6-cu-ft-ai-laundry-hub-large-capacity-single-unit-washer-with-flex-auto-dispense-system-and-7-6-cu-ft-gas-dryer-in-brushed-black-sku-wh46dbh500gva3/)). The identity matches, so
the 103-vs-95 difference remains a real source-field conflict, not an SKU join
failure. The live page extraction did not expose the annual-energy number itself;
103 comes from the hash-bound exact-SKU PDP Specs/Support capture.

The next rule decision is limited to two G3 cases: severity for an annual kWh
conflict and treatment of an SKU absent from the current EPA cohort. No such
assessment has been applied. PDP annual-kWh omissions with agreeing label/EPA
values remain mapped to the previously requested LOW behavior for later
assessment. Recommended model for rule definition: Sol medium; Luna low suffices
for further mechanical source comparison.

## Approved assessment result (2026-09-22)

The final Washer assessment workflow
[35687295557](https://github.com/Empty-Bell/RDA/actions/runs/35687295557), commit
`b9755d8`, applied the approved rules to all 37 same-run exact SKUs:

- annual-energy disagreement = MEDIUM;
- PDP annual-energy missing while label and EPA agree = LOW;
- EPA current absent and any PLP logo, PDP logo, or spec certification claim
  present = HIGH;
- ENERGY STAR registered with any publication point absent = LOW consistency;
- no finding is displayed and counted as PASS.

Result: HIGH 0, MEDIUM 2, LOW 5, PASS 30. The MEDIUM rows are
`WH46DBH500EVA3` and `WH46DBH500GVA3`. The LOW rows are
`WA54CG7105AVUS`, `WA54CG7105AWUS`, `WF90F53ADSA5`, `WF90F53ADYA5`, and
`WW25FG6B34BEA2`. `WF90F53ADYA5` has both a missing-PDP-energy finding and an
ENERGY STAR publication-consistency finding, but the SKU display outcome remains
LOW. The 8 EPA-current-absent rows have all three publication points absent, so
they are PASS under the approved conditional HIGH rule. The rule remains active:
if any publication point becomes present while EPA current remains absent, the
SKU becomes HIGH automatically.

Status: bounded source reconnaissance PASS on hosted Ubuntu (run 35104751514).
Phase 0 remains RUNNING. Certification matching/compliance NOT_EVALUATED.

Official discovery references:
- Samsung listing: https://www.samsung.com/us/laundry/washers/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-clothes-washers
- EPA metadata: https://data.energystar.gov/api/views/bghd-e2wd.json
- EPA sample: https://data.energystar.gov/resource/bghd-e2wd.json?$limit=3
- Separate combo dataset: https://data.energystar.gov/w/9jai-gs6t/im48-wy4k

Runtime uses installed-version desktop Linux Chromium UA, cold hosted Ubuntu 24.04,
bounded retries and no LLM. Category and bridge group identities are observed from
actual page requests. All source variants retain exact SKU and group provenance.
Terminal pagination and unique DOM tile groups must match the observed API total.

EPA schema observed directly from the official metadata: annual_energy_use_kwh_year,
date_qualified (display name Date Certified), integrated_modified_energy_factor_imef,
integrated_water_factor_iwf and annual_water_use_gallons_year. Energy is per year;
annual water must not be compared to dishwasher water per cycle.
Metadata identity/schema will also be revalidated on hosted Ubuntu.

The washer listing may include all-in-one and stacked products. Do not force every
listing SKU into a standalone residential washer certification dataset. Catalog
presence, qualified date and sample availability do not prove active certification.
Combo routing and washer-versus-dryer label selection require source evidence before
matching. No new compliance rule or issue code is introduced in this reconnaissance.

## First hosted observations

Run https://github.com/Empty-Bell/RDA/actions/runs/35104059834, commit 920c22e,
all three family jobs succeeded. Washer category_code `08010000` and taxonomy_code
`08010100` were observed in POST pf_search. Retain both request keys: category alone
does not define this washer listing. Pagination offsets 0/14, request counts 14/16,
responses 14/4; total 18 API groups = 18 unique rendered tile groups, 37 exact SKUs.
Visible representative links only 14; do not use them as a population count.
These are observed snapshot counts, never production constants.

First target WD90F53AVBUS is an all-in-one vented washer/electric dryer combo,
identified from the source PDP URL and rendered page. Bridge group_id `569348`.
Exact Specs: `Energy Guide Label` = `103 kWh/year`, `Total Capacity (cu. ft.)` = `5.3`,
`Energy Gallons / Year` = `4500`, ENERGY STAR Certified = `Yes`. Preserve odd source
names verbatim; do not silently rename Energy Gallons / Year as an energy quantity.
The exact Support record contains an EnergyGuide PDF despite zero rendered anchors.

PDF https://images.samsung.com/is/content/samsung/p6pim/us/wd90f53avbus/energyguide/us-energyguide-wd90f53avbus-550443963.pdf
HTTP 200/application/pdf, 974330 bytes; SHA256
`f096d0692929654d41f158a15ebb368095f63b8dd9aa70c24c6e65449d398658`.
Embedded text empty; 2x RapidOCR fallback. Visually verified US Clothes Washer label:
model WD90F53AV*, 103 yearly kWh, 5.3 cubic feet, Standard capacity class, $14 electric
water-heater cost and $11 natural-gas-water-heater cost. Label expressly limits
comparison to yellow-number labels based on the same test procedures. Preserve test
basis/label generation before cross-product or historical energy comparisons (D01).
This washer label is not a measurement of complete wash-plus-dry electricity use.

Artifact 10448694403 (1072039 bytes), ZIP SHA256
`70f6a8a65267056b54e6f829e6d390be454b70d7414736b066687e2d541dd122`.
Raw PDF/render artifact expires 2026-09-30. Matching, quantitative discrepancy rules,
all-in-one/stacked certification routing and full field quality remain NOT_EVALUATED.

## Additional standalone sample / partial-text regression

Run 35104431554 (77a32f0), washer job source checks PASS, 36 hosted tests.
Source-backed standalone-path sample WF90F53ADSA5 has an exact Specs/Support record,
5.3 cubic feet and distinct raw Certified/Most Efficient claims. No Energy Guide Label
annual-energy spec was observed; preserve absence as UNKNOWN and do not borrow combo
103 kWh. Stacked products and top-load samples are not yet individually verified.

PDF https://images.samsung.com/is/content/samsung/p6pim/us/wf90f53adsa5/energyguide/us-energyguide-wf90f53adsa5-554563643.pdf
HTTP 200/application/pdf, 620278 bytes; SHA256
`349fa031c9f91854532cc39757cc988255565dee2227ed5e7b14c449335f7c6a`.
Its long embedded text includes model/capacity/test-basis text but omits energy/cost
numbers. That prior extraction is preserved in partial-text-energyguide.json.
Recon OCR fallback now detects missing numeric kWh even with long embedded text,
records MISSING_ENERGY_VALUE_IN_EMBEDDED_TEXT and preserves both extraction layers.
This basic health trigger is not a complete field-quality gate: field coordinates,
label region, all PDF pages, identity/wildcard rules and numeric selection remain open.

The same run's refrigerator job FAIL detected one source group repeated across
offsets 14/30 (MULTI_GROUP_ID_601372); 41 rows but only 40 unique groups. Source
request category/filter/sort matched across pages. Do not deduplicate and declare a
complete population or weaken the gate. Raw failed artifact 10449547305 preserved;
ZIP SHA256 c6bc6e165e9192dddbb713d9b7a07bb7d29f0016deeb294f872d7741076c6a39.
API snapshot/pagination consistency remains an open source-health condition.

## Final hosted validation

https://github.com/Empty-Bell/RDA/actions/runs/35104751514
Commit eb0689f9d392e310875afb8d1378f62fcc7f9ad7, washer job 104822950139.
39 tests plus all five washer source checks and artifact upload PASS; refrigerator
and dishwasher regression jobs also PASS. Earlier duplicate-group failure remains
in the evidence record; a later successful snapshot does not prove permanent stability.

Standalone PDF OCR now records MISSING_ENERGY_VALUE_IN_EMBEDDED_TEXT and recovers
103 kWh/year; render visually checked model WF90F53*D*, 5.3 cubic feet, $14/$11
water-heater costs and same-test yellow-number text. PDP annual-energy absence remains
UNKNOWN despite a valid label value. Certified and Most Efficient raw claims remain
independent, with neither evaluated against EPA in this phase.

Final washer artifact 10448949688 (1749287 bytes), ZIP SHA256
`1c209031a4655a016a4da0df7ef623fad91ea17ea26a0c47d242724231b92464`.
Compact evidence: docs/evidence/washer-source-recon.json; per-fixture SHA256/source
run IDs: docs/evidence/washer-fixture-manifest.json. Raw evidence expires 2026-09-30.
Only combo and front-load sample PDPs verified, not all 37 products. Top-load/stacked
label contracts, combo dataset applicability, withdrawal/wildcard/market matching and
complete PDF field-quality gates remain open. Next bounded product group: Television.
