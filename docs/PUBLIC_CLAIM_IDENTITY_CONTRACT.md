# Independent public claim and PDP identity reconnaissance

Status: bounded hosted discovery PASS; Phase 0 RUNNING; claim consistency and
certification NOT_EVALUATED. No new regulatory rule or issue code.

Observe and preserve independently:
1. Exact listing variant modelCode/modelName, ecomFlag, stockFlag and energyStarFlg.
2. Rendered listing card SKU/title and visible ENERGY STAR text/image candidates,
   scoped to the observed product-card ancestor. Variant coverage is not inferred.
3. Current PDP visible h1 headings and Product JSON-LD SKU/MPN/name/availability.
4. Direct ENERGY STAR scalar fields on explicitly modelCode-identified records
   from public Samsung bridge-data/ecom-data responses. Record section and URL.
5. Exact-SKU spec-table ENERGY STAR name/value pairs.
6. Visible page ENERGY STAR text/image candidates. Page candidates can include
   navigation, related products, marketing or footer; attribution remains NOT_EVALUATED.

Product-only snapshots are saved before interpretation. Do not save full DOM,
arbitrary network payloads, account/chat data, unrelated JSON-LD or offer prices.
JSON-LD projection retains Product identifiers/name/availability and only ENERGY STAR
additionalProperty pairs. Nonempty SKU/MPN identifiers must all agree with the
target; contradictory identifiers remain unattributed. Title similarity and URL alone
never establish the current product. JSON-LD parser errors fail the observation check.

PLP Y/N, ecomFlag/stockFlag, spec claim and raw PDP flags remain source values;
their truth/current-certification/commerce mapping is not defined by this collector.
No observed structured flag means NOT_EVALUATED, not false. Empty visible candidates
mean no candidate in the current mounted DOM, not proof of absence after full page
interaction. Headings can be marketing/product-group names rather than exact SKU titles.
Available structured records cannot substitute for the existing PDP identity gate.

Intermediate evidence: public-claim-snapshot.json, public-claim-facts.json,
plp-claim-observation.json and recon.json per source leg. Existing population/PDP
contracts and sampled SKU limits remain. Standard ubuntu-24.04 x64 and desktop
Chromium identity are unchanged; runtime makes no LLM calls.

Next validation after discovery: actual fixture contracts, independent rendered
badge attribution and structured field coverage. Preserve disagreement without
choosing one source as certification truth. Full SKU collection and EPA matching
are downstream work.

Final hosted acceptance: https://github.com/Empty-Bell/RDA/actions/runs/35160456564,
commit 8b1ee4d0a798179a64486b782f0c0709225597ea. 126 tests and all 12 source jobs
for 11 product groups passed. Three product-only actual fixtures (refrigerator,
dishwasher, Tablet), source-run/SHA256 manifest and initial failure history are
versioned. Initial run 35160080596 had a Computer selected-control loading timeout;
the dependent claim observation failed, not an absence result. One bounded reload
is now allowed only for selected-control loading timeout, with per-attempt selection
evidence and source errors preserved. Exact selected/purchase/backend SKU gates
remain unchanged. An identity mismatch is not retried into a different configuration.

RF29DB9900QDAA: listing modelName RF29DB9900QD differs from the rendered product
title; exact Product JSON-LD supplies SKU, name and raw schema.org InStock.
DW90F89P0USRAA likewise has exact Product JSON-LD and a spec ENERGY STAR Certified
Yes value. Both have PLP Y plus a visible logo candidate. SM-X930NZAAXAR has PLP Y,
an exact Product JSON-LD and a visible logo candidate, but no sampled spec-table
ENERGY STAR field. These differences are observations, not claim conflicts or EPA
findings. The Tablet PLP cards have observed card scopes but no sampled mounted-DOM
ENERGY STAR candidates; this is not proof of no public claim.

Subsequent bounded primary badge attribution and nested field discovery are covered
by CLAIM_ATTRIBUTION_SOURCE_CONTRACT.md (run 35162114501). The exact inline
product energyStarFlag source is now observed on all primary samples, separately
from earlier unobserved direct bridge fields. Unsupported surfaces
and flag interfaces outside that scope remain unknown. Define normalized commerce
semantics only with actual source evidence. Broad page candidates, absent
fields and missing exact JSON-LD remain distinct from source access/parsing errors.
Compact final evidence is docs/evidence/public-claim-identity-recon.json; raw
artifacts retain their recorded 14-day expiry. Full G0 is still NOT_EVALUATED.

All 12 source legs had one exact Product JSON-LD record for their primary PDP
sample. Direct modelCode-identified ENERGY STAR fields were unobserved in all
samples and remain NOT_EVALUATED. Samples with spec claims: refrigerator,
dishwasher, washer/combo, dryer/combo and range. Computer/Chromebook/Tablet
samples had PLP Y and PDP logo candidates without spec claims. TV/cooktop/hood/
monitor primary samples had PLP N and no mounted-DOM PDP candidates. These are
sample observations, not family-wide absence or certification findings. Positive
PLP card candidates existed on other TV/cooktop cards and must retain their own SKUs.
