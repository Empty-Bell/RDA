# Clothes Dryer EPA-focused source reconnaissance

Status: RUNNING; Phase 0. Certification matching/compliance NOT_EVALUATED.

Official sources:
- Samsung listing: https://www.samsung.com/us/laundry/dryers/
- Catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-clothes-dryers
- EPA metadata: https://data.energystar.gov/api/views/t9u7-4d2j.json
- EPA sample: https://data.energystar.gov/resource/t9u7-4d2j.json?$limit=3

Official metadata identifies t9u7-4d2j Certified Residential Clothes Dryers.
Preserve product_type, type (Fuel Type), drum_capacity_cu_ft, combined_energy_factor_cef,
estimated_annual_energy_use_kwh_yr and date_qualified (Date Certified) independently.
CEF is efficiency, not annual kWh. Fuel values and complete current-certification
applicability/matching require later evidence. Combo/stacked products must not be
forced into standalone dryer certification solely from listing membership.

Actual category/taxonomy/bridge IDs come from the live page requests. Terminal API
population and unique rendered tile groups must reconcile; retain exact variants.
Exact Specs/Support is probed; EnergyGuide PDF is OUT_OF_RECON_SCOPE in this EPA-only
reconnaissance. No legal applicability conclusion is made from that probe scope.
Cold hosted Ubuntu 24.04, version-matched desktop Chromium UA, no runtime LLM.
See SOURCE_COVERAGE.md: this is population discovery plus sample verification,
not full per-model PDP/label collection or EPA SKU lookup.
