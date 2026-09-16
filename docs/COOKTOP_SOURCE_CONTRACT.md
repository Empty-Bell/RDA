# Cooktop EPA-focused source reconnaissance

Status: RUNNING. Phase 0; certification matching/compliance NOT_EVALUATED.

Official sources:
- Samsung listing: https://www.samsung.com/us/cooking-appliances/cooktops/
- Catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-electric-cooking-products
- EPA metadata: https://data.energystar.gov/api/views/m6gi-ng33.json
- EPA sample: https://data.energystar.gov/resource/m6gi-ng33.json?$limit=3

Same residential electric cooking dataset as Range; product_type and cooking_top_technology
remain independent routing data. Commercial electric cooktops nt9t-yxu3 do not substitute.
Gas sales SKUs must remain in the source population without assuming certification
applicability. Total annual energy and oven/cooking-top low-power component energy
are preserved independently; component absence in a Cooktop row is not schema absence.

Actual category/taxonomy and bridge group IDs come from page requests. Reconcile
terminal pages and unique DOM/source groups. Exact Specs/Support modelCode selects
sample facts and preserves claim/fuel/cooktop types. EnergyGuide PDF validation is
OUT_OF_RECON_SCOPE for this EPA_ONLY reconnaissance, not a legal applicability ruling.
Hosted cold Ubuntu 24.04, desktop version-matched Chromium UA, no runtime LLM.

Coverage limits: see [SOURCE_COVERAGE.md](SOURCE_COVERAGE.md). This probe verifies
listing population and sample PDP/schema, not all-model fact collection or EPA lookup.
