# Cooktop EPA-focused source reconnaissance

Status: bounded Cooktop source reconnaissance PASS on hosted Ubuntu (35107565285).
Phase 0 remains RUNNING; certification matching/compliance NOT_EVALUATED.

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

## First hosted source observation

https://github.com/Empty-Bell/RDA/actions/runs/35107226599, commit 126e7c2,
cooktop job 104831484833 all four source checks PASS. Actual pf_search request
category_code 08080000, taxonomy_code 08080300; same category as Range but distinct
taxonomy. Preserve both and do not substitute range taxonomy 08080200. Offset 0,
requestCount 14, returned 9, hasMoreResults=false; 9 API groups = 9 distinct rendered
tile groups, 20 exact SKUs. Only 3 representative visible links; not a population count.
Counts are fixture observations, not production targets.

First exact sample NA30N6555TS/AA is gas, bridge-data group_id 572596. Cooktop Type
Gas observed. Preserve slash/suffix in modelCode; URL hyphen form is not exact identity.
No EnergyGuide metadata; EPA-only probe is OUT_OF_RECON_SCOPE. No annual-energy or
dedicated structured certification claim inferred. Electric sample is independently
selected from observed electric-cooktop source URL, not a model-prefix matching rule.

Initial artifact 10450911656, 11807 bytes; ZIP SHA256
e3bdee7d5e94891a935ba6bafec33e8c6ae92b07a508ead9655623a2956f4e2f.
Raw source artifact expires 2026-09-30. Full model collection, induction sample PDP,
gas/electric eligibility, current EPA candidate matching and rendered claim contracts
remain open. EPA sample remains a generic schema sample, not a Samsung product lookup.

## Final hosted acceptance

https://github.com/Empty-Bell/RDA/actions/runs/35107565285
Commit d6fb2a490e363f24c00df29d9e05f648d4b18f1f, cooktop job 104832622093.
62 tests, all five cooktop source checks and artifact upload PASS. Additional source
URL-selected electric sample NZ30K7570RS/AA uses bridge group_id 568357, exact Specs/
Support. Cooktop Type Radiant appears twice in raw spec pairs; retain both. No ENERGY
STAR spec claim observed, so structured claim remains UNKNOWN, not certification false.
Both gas/electric samples keep EnergyGuide validation OUT_OF_RECON_SCOPE.

Final artifact 10450499421 (16047 bytes), ZIP SHA256
42739e7c6a2955370372ac7592ba7176642f144287caf4d61bc58457edd109f8.
Public compact source observations: docs/evidence/cooktop-source-recon.json;
fixture hashes/source run IDs: docs/evidence/cooktop-fixture-manifest.json.
Large/raw evidence expires 2026-09-30. Next bounded source group: Clothes Dryer.
Source reconnaissance PASS is not per-model collection or compliance PASS;
see SOURCE_COVERAGE.md for the actual collected/verified coverage.
