# Range EPA-focused source reconnaissance

Status: bounded Range source reconnaissance PASS on hosted Ubuntu (35106676958).
Phase 0 remains RUNNING; certification matching/compliance NOT_EVALUATED.

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

## First hosted observations

https://github.com/Empty-Bell/RDA/actions/runs/35106401657, commit 55aafbf,
range job 104828640045 all four source checks PASS. Actual POST pf_search uses
category_code 08080000 and taxonomy_code 08080200. Preserve both; category alone
does not define the source population. Offsets 0/14, request counts 14/16, returned
rows 14/5, terminal total 19 groups = 19 distinct rendered groups, 58 exact SKUs.
Representative visible links only 14. Counts are snapshot assertions, not constants.

Sample NSE80H63XRAA exact PDP observes bridge-data group_id 600531. Specs provide
Fuel Type Electric, Cooktop Type Electric, Oven Capacity 6.3 cu. ft., ENERGY STAR
Certified Yes (source name includes a nonbreaking space). Preserve raw claim separately
from any EPA determination. No annual-energy spec or EnergyGuide document observed;
EnergyGuide probe OUT_OF_RECON_SCOPE under this task's EPA_ONLY scope.

EPA m6gi-ng33 has 40 public columns. First three-row sample includes LG Cooktop
model CBIS3618*E: annual energy 189 kWh/year, cooking-top low-power 5.00 kWh/year,
oven component omitted in that row. Metadata column presence and per-row optional
component absence are different contracts. Sample is not a Samsung range lookup.
The dataset's product_type is needed before treating an EPA row as a range candidate.

First range artifact 10450014270, 17837 bytes, ZIP SHA256
feba4931fa5acb63dc31aa78e577446a2f3d058687b862366c3ea90923d48566.
Raw source evidence expires 2026-09-30. Gas/dual-fuel sample PDPs, complete per-SKU
coverage, electric eligibility/routing, current/withdrawn/market/wildcard matching,
rendered claim and dedicated structured claim contracts remain open.

## Final hosted validation

https://github.com/Empty-Bell/RDA/actions/runs/35106676958
Commit 7ca2c669b7c194da59451d32fcbc87fd4a3d1dd8, range job 104829597830.
54 tests, all four range source checks and artifact upload PASS on cold hosted Ubuntu.
All five family jobs in this final run concluded success.
Final artifact 10449978862 (17875 bytes), ZIP SHA256
89bf7159439c9d82f82603d878848d8ac08994cd5c95ac21d3cd192efd51310e.
Compact evidence: docs/evidence/range-source-recon.json. Per-fixture hashes/source
run IDs: docs/evidence/range-fixture-manifest.json. Raw evidence expires 2026-09-30.
Only one electric sample PDP is verified, not all 58 SKUs or gas/dual-fuel applicability.

Next bounded source group: Cooktop. The shared residential electric cooking dataset
does not eliminate the need to independently observe its Samsung listing/PDP and
product-type contracts. Existing exploratory Sol medium guidance applies; no LLM
calls in hosted audit runtime.
