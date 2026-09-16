# Tablet EPA-focused source reconnaissance

Status: hosted observation pending; Phase 0 RUNNING; certification NOT_EVALUATED.

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

Initially reuse the Computer selected-SKU/visible Continue control and observed
ecom-data group provenance contract; do not click purchase controls. Request Specs
through the observed public pattern and select exactly one matching modelCode in
the array. Retain product-only modelCode/groupName/name/value fields. Specs-only
Support remains NOT_EVALUATED, document count null. Hosted evidence must establish
whether this contract is supported on the current Tablet buy page.

Preserve battery mAh versus Wh, charger/output W, measured mode W and EPA TEC kWh
as separate facts. Do not convert mAh to Wh without voltage, battery capacity to
annual consumption, or advertised playback duration to certification measurements.
Retain all raw spec pairs before defining Tablet field projections. Generic EPA
rows may be desktops from other brands: they establish access/schema only, not
Tablet candidates or Samsung certification. Type/markets/current status/variant
matching require later contracts. EnergyGuide is OUT_OF_RECON_SCOPE in this EPA-only
reconnaissance; this is not a legal applicability finding.

Runtime: standard cold ubuntu-24.04 x64, actual-version desktop Chromium user agent,
en-US, pinned bootstrap, no LLM calls. Counts and identifiers in evidence are snapshots,
never production constants. Preserve failed observations before changing collectors.
