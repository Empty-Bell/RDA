# Tablet EPA-focused source reconnaissance

Status: exact-SKU hosted PDP collection PASS (50/50); EPA candidate capture is
source-only and certification/registration/publication assessment remains
NOT_EVALUATED. Formal G3/G4 acceptance is not implied.

Official sources:
- Samsung https://www.samsung.com/us/tablets/ links All Tablets through
  /us/mobile/tablets/all-tablets/ to https://www.samsung.com/us/tablets/all-tablets/.
- EPA https://www.energystar.gov/products/computers explicitly includes slate/tablets
  in the Computers specification. Android OS alone does not establish product type.
- Catalog https://catalog.data.gov/dataset/energy-star-certified-computers-v9-0
- Metadata https://data.energystar.gov/api/views/rxdj-2c88.json
- Generic sample https://data.energystar.gov/resource/rxdj-2c88.json?$limit=3

Require terminal browser-observed pf_search pages, stable totals, unique API groups
and reconciliation with rendered product-card groups. Static HTML contains example
placeholders and is not population evidence. Preserve exact color/storage/connectivity
SKUs and their source PDP URLs. Consumer listing is not exhaustive business, rugged,
support or carrier catalog coverage.

Reuse the hosted-verified Computer selected-SKU/visible Continue control and observed
ecom-data group provenance contract; do not click purchase controls. Request Specs
through the observed public pattern and select exactly one matching modelCode in
the array. Retain product-only modelCode/groupName/name/value fields. Specs-only
Support remains NOT_EVALUATED, document count null.

Preserve battery mAh versus Wh, charger/output W, measured mode W and EPA TEC kWh
as separate facts. Do not convert mAh to Wh without voltage, battery capacity to
annual consumption, or advertised playback duration to certification measurements.
Retain all raw spec pairs before defining Tablet field projections. Generic EPA
rows may be desktops from other brands: they establish access/schema only, not
Tablet candidates or Samsung certification. Type/markets/current status/variant
matching require later contracts. EnergyGuide is OUT_OF_RECON_SCOPE in this EPA-only
reconnaissance; this is not a legal applicability finding.

EPA candidate capture may preserve the complete current Samsung Computers V9.0
cohort and link only a case-sensitive literal full-SKU equality. EPA strings
containing `*` remain raw and are not interpreted as wildcard matches (open
DECISIONS D09/D11). Prefix/family equivalence is not applied by this extractor;
those relationships remain NOT_EVALUATED pending an approved contract.
Candidate rows remain source evidence; product type,
US market, certification status, carrier/storage/color variant relationships,
publication severity, and overall compliance stay NOT_EVALUATED until reviewed
contracts approve those semantics.

Runtime: standard cold ubuntu-24.04 x64, actual-version desktop Chromium user agent,
en-US, pinned bootstrap, no LLM calls. Counts and identifiers in evidence are snapshots,
never production constants. Preserve failed observations before changing collectors.

Initial run https://github.com/Empty-Bell/RDA/actions/runs/35158772571,
commit 7327d88f53ea6488eedb11668f241e895ab00094, Tablet job 105004393163:
four live checks PASS, 11 API groups = 11 rendered groups, 50 exact SKUs,
terminal first page, category_code 01020000, requestCount 22. Sample
SM-X930NZAAXAR selected model/storage controls and visible Continue match exactly;
body SKU text is absent and is not used alone as identity. Specs retain Android,
12 GB RAM, 256 GB storage, Wi-fi, main display 2960 x 1848 (WQXGA+), battery
11600 mAh and advertised playback Up to 23 hours. No annual energy, Wh conversion,
charger rating, structured ENERGY STAR claim or Support absence is inferred.
EPA has 68 columns and three generic rows, not Samsung candidates.

Five public fixtures and their SHA256/source run manifest are versioned; 12 Tablet
regressions bring the full suite to 115 tests. Initial whole run had a Chromebook
selected-control timeout (no selected controls, visible Continue alone), preserved in
tablet-regression-failure-history.json. Tablet success does not mask that failure.

Final acceptance https://github.com/Empty-Bell/RDA/actions/runs/35159081725,
commit 76d0e271c58a9a02f88efaa3447101168b6dcf40, Tablet job 105005374161:
115 tests and four live Tablet checks PASS; all 12 source jobs for 11 product groups
succeeded. Chromebook recovered without changing the selected-SKU identity gate;
one successful retry does not establish source reliability. Tablet artifact 10472485653,
19019 bytes, ZIP SHA256
85b5caf87a40e8f80d2194a713e65db921d19ab0de01c8a3f961411b59db05db,
expires 2026-09-30T22:45:08Z. Compact facts/provenance and recovery evidence are in
docs/evidence/tablet-source-recon.json. Full G0 remains NOT_EVALUATED.
