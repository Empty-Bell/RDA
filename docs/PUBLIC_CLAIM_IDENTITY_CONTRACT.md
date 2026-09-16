# Independent public claim and PDP identity reconnaissance

Status: hosted discovery pending; Phase 0 RUNNING; claim consistency and
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
additionalProperty pairs. Exact SKU/MPN is required; title similarity and URL alone
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
