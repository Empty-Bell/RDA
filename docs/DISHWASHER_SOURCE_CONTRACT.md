# Dishwasher source reconnaissance

Status: bounded live source reconnaissance PASS (run 35103320640).
Phase 0 remains RUNNING; certification matching and compliance NOT_EVALUATED.

Discovery references:
- Samsung official listing: https://www.samsung.com/us/dishwashers/all-dishwashers/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-dishwashers
- Official certified dataset: https://data.energystar.gov/w/q8py-6w3f/im48-wy4k
- Most Efficient dishwasher dataset is separate (butk-3ni4); never substitute it.

Hosted checks use the same installed-version desktop Linux Chromium UA as refrigerators.
The category code and bridge request group ID must come from actual page requests.
No request identity is derived from the refrigerator source. Current population is
accepted only if terminal pagination, API groups and unique rendered tile groups reconcile.

Exact PDP Specs and Support records are selected by modelCode. All observed spec
name/value pairs are preserved because refrigerator-specific capacity names cannot
define dishwasher capacity or annual-energy contracts. Original PDF and extraction
text remain in artifacts; automated field parser quality is NOT_EVALUATED.

EPA metadata must identify q8py-6w3f by ID and certified residential dishwasher name.
Schema checks preserve numeric strings and verify brand/model/unique ID, annual
energy, markets and certified-date columns. Sample availability does not define a
current certification or support any Samsung model match.

Sanitized fixtures and regression tests are versioned in tests/fixtures/dishwasher
and tests/test_dishwasher_contract.py. Full Phase 0 remains RUNNING.

## Observed Samsung contracts, first hosted run

Run https://github.com/Empty-Bell/RDA/actions/runs/35102983525, commit a7601ff.
Samsung checks PASS; EPA schema check FAIL because refrigerator column names do
not apply. This failure is retained, not relabeled as PASS.

POST pf_search uses category_code `08090000`, startIndex `0`, requestCount `14`;
response contains 9 groups, 21 unique exact SKUs, hasMoreResults=false. Rendered
9 card-name elements map to 9 distinct API groups. Visible representative URL
count is only 6 and must not define population size. Counts are fixture observations.

Sample modelCode `DW90F89P0USRAA`; observed bridge-data request group_id `575427`.
The exact Specs record provides `Energy Usage (kWh/year)` = `225`, `Place Setting`
= `16`, `Water Consumption (gallons/cycle)` = `2.9`, ENERGY STAR Certified = `Yes`.
Do not reuse refrigerator capacity or energy names. All spec pairs retain provenance.
No rendered EnergyGuide anchor was found; the exact Support record independently
contains the PDF. Missing DOM anchor does not prove missing disclosure.

PDF https://images.samsung.com/is/content/samsung/p6pim/us/dw90f89p0usraa/energyguide/us-energyguide-dw90f89p0usraa-554563789.pdf
returned 200/application/pdf, 982370 bytes; SHA256
`fa6be00fcbad37f662ffeb80d9efc6b641d72c04e3801eba24548e1e42164591`.
Empty embedded text requires 2x RapidOCR. Render visually checked: US yellow label
model `DW90F8**0***`, annual electricity 225 kWh, capacity category Standard,
annual electric-water-heater cost $32 and gas-water-heater cost $22.

**Mixed-region PDF:** one page includes both US EnergyGuide and Canadian EnerGuide,
plus print instructions. Whole-page OCR interleaves both regions. Future field
extraction must retain bounding boxes and identify the US label region before
selecting any kWh/model/cost/mark. Repeated 225 observations do not prove US field
location. Label capacity category Standard and PDP 16 place settings are different
quantities, not a raw-value mismatch. Wildcard matching remains NOT_EVALUATED.

## Observed EPA schema difference

Refrigerator: annual_energy_use_kwh_yr / date_qualified.
Dishwasher: annual_energy_use_kwh_year / date_certified.
Dishwasher additionally exposes capacity_maximum_number_of_place_settings and
water_use_gallons_cycle. Unit/period are different; water is per cycle, energy per year.
These are observed metadata contracts; certification currency, Samsung matching,
withdrawal status and pagination over the complete EPA population remain unverified.

Metadata: https://data.energystar.gov/api/views/q8py-6w3f.json
Sample: https://data.energystar.gov/resource/q8py-6w3f.json?$limit=3
Observed rowsUpdatedAt: 1789564310; sample AEG F8242FI energy `234`, water `3.00`,
place settings `15`, markets `United States, Canada`. This is a schema sample;
it is not an EPA candidate lookup for the Samsung PDP.

Successful live run 35103320640 artifact 10449725058 (1329938 bytes), ZIP SHA256
`cdcd8366a559ef32f6650d3bb8df421a776208e56013a804e762cd6b0213ba68`.
Original PDF and OCR render expire on 2026-09-30; compact source observations and
manual region check are in docs/evidence/dishwasher-source-recon.json.
Fixture hashes and source run IDs: docs/evidence/dishwasher-fixture-manifest.json.

Next: Clothes Washer bounded source reconnaissance. Use the existing Sol medium
exploration guidance; use Terra medium after contracts are fixed. Runtime uses no LLM.

Final 28-test hosted dishwasher validation PASS:
https://github.com/Empty-Bell/RDA/actions/runs/35103625881
commit 629e3a6a21baa1a39f03e4bd61d0435640b30189, job 104819058726.
All four live source checks and artifact upload passed on cold hosted Ubuntu.
