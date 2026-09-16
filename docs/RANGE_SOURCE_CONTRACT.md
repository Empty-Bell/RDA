# Range EPA-focused source reconnaissance

Status: RUNNING. Phase 0; certification matching/compliance NOT_EVALUATED.

Official discovery:
- Samsung listing: https://www.samsung.com/us/cooking-appliances/ranges/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-electric-cooking-products
- EPA metadata: https://data.energystar.gov/api/views/m6gi-ng33.json
- EPA sample: https://data.energystar.gov/resource/m6gi-ng33.json?$limit=3
- Eligibility: https://www.energystar.gov/products/electric_cooking_products/key_product_criteria

Dataset m6gi-ng33 identifies certified Residential Electric Cooking Products.
Commercial electric cooktops (nt9t-yxu3) are a separate certification population.
Preserve product_type, cooking_top_technology, annual_energy_consumption_kwh_yr,
low_power_mode_energy_consumption_oven_kwh_yr and
low_power_mode_energy_consumption_cooking_top_kwh_yr independently. Annual total
and component low-power energy are not synonyms. Date Certified is date_certified.

The sales listing can contain gas/electric/dual-fuel products; do not discard gas
SKUs or force all listing products into this electric dataset. Applicability,
fuel/product classification and certification matching remain later contracts.
This task is EPA_ONLY under the master plan. Exact PDP Specs/Support and claims
are probed; EnergyGuide metadata remains observable but a PDF is not a required
acceptance gate. OUT_OF_RECON_SCOPE is not a legal applicability determination.

Actual source category/group/pagination must come from page requests. Terminal
pagination, unique source groups and distinct rendered tile groups must reconcile.
Runtime uses cold hosted Ubuntu 24.04 and desktop version-matched Chromium UA;
no local persistent browser state or runtime LLM is required.
