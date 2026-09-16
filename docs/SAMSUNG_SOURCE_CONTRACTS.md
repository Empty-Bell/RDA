# Samsung source contracts — refrigerator, dishwasher, washer and TV reconnaissance

Observed on GitHub-hosted Ubuntu 24.04 x64, 2026-09-16. Refrigerator contracts below;
Dishwasher contracts: [DISHWASHER_SOURCE_CONTRACT.md](DISHWASHER_SOURCE_CONTRACT.md).
Washer contracts: [WASHER_SOURCE_CONTRACT.md](WASHER_SOURCE_CONTRACT.md).
TV contracts: [TV_SOURCE_CONTRACT.md](TV_SOURCE_CONTRACT.md).
Other 7 product groups remain UNKNOWN. No compliance semantics implemented.

## PLP / pf_search

Entry: `https://www.samsung.com/us/home-appliances/refrigerators/all-refrigerators/`
redirects to `https://www.samsung.com/us/refrigerators/all-refrigerators/`.

Observed endpoint: `POST https://sribsrch.ecom.samsung.com/estoresearch-api/v1/scom/us/pf_search`.
Source is page network, not a historical guessed endpoint. Re-observe when it drifts.

Observed public JSON request fields:

```json
{
  "clientCode": "b2c", "clientName": "scom_pf", "firstSearchYN": "true",
  "countryCode": "us", "storeID": "us", "startIndex": "0",
  "requestCount": "14", "category_code": "08030000",
  "filters": "[]", "sort": "recommended"
}
```

Pagination observed: string startIndex `0 → 14 → 30`; requestCount `14 → 16 → 16`;
returned records `14 → 16 → 11`; searchTotalCount 41. These are historical fixture
observations, not production constants. UI scroll can trigger the next request before
an explicit View More click; reconcile newly observed responses before clicking again.
These pages contain 75 unique exact SKUs. Count drift and inconsistent repeated page
offsets are explicit contract failures. An identical repeated request is retained as
an observation, not counted as an additional page.

| Meaning | Response field / contract |
|---|---|
| total/terminal | root searchTotalCount integer, hasMoreResults boolean |
| representative tiles | searchResults[] |
| representative exact SKU | searchResults[].modelCode (not shorter modelName) |
| source grouping ID | searchResults[].group_id |
| variant collection | searchResults[].groupedProductList[]; includes representative |
| exact variant SKU | groupedProductList[].modelCode |
| PDP URL | groupedProductList[].pdpURL, resolved against www.samsung.com |
| commerce | ecomFlag, stockFlag; preserve raw Y/N/unknown |
| PLP claim | energyStarFlg; preserve independently per exact SKU |

Example: group MULTI_GROUP_ID_601337, representative RF29DB9900QDAA,
variants RF29DB9900QDAA/RF29DB990012AA/RF23DB990012AA/RF23DB9900QDAA.
Missing variants, duplicate SKU, different grouping, absent pagination fields,
drifted total, missing terminal page, listing URL in place of PDP are contract errors.
Duplicate groups across pages must be surfaced; never quietly lose source provenance.

41 Results is rendered on the PLP and equals the observed API group total.
Observed per-card name selector: `.pd21-product-card__name`, attribute `data-modelcode`.
Wait for DOM mounting after API delivery and map each tile SKU to its population group.
A selected tile SKU may differ from the pf_search representative. Counting only visible
links to representative URLs found 29 even with 41 API groups; it is not a tile count.
Final hosted run 35101976503 verified 41 card-name elements, each mapping to exactly
one group, with 41 distinct groups = API total = rendered 41 Results.

## PDP / bridge-data

Use the exact PDP URL from the population response. A listing/support redirect is not a PDP.
The first probe's link heuristic selected a listing; that was not bridge contract validation.
The new reconnaissance navigates the pf_search product URL and supports exact target SKU
with rendered text plus an exact matching Specs/Support record.

Observed GET endpoint on sample PDP:
`https://www.samsung.com/us/gapi/v1/bridge/cacheable/bridge-data`
with query `data_type=Specs,Support,RelatedModels`, `store_type=B2C`,
`group_id=580109`, `version=v2`.

**PDP group_id 580109 differs from PLP MULTI_GROUP_ID_601337.** Discover PDP request identity
from its network. Do not strip the PLP prefix and guess the PDP request key.
Payload returns multiple siblings; select exact modelCode, never the first element.
RelatedModels is not current population and is omitted from committed fixtures.

| Meaning | Field |
|---|---|
| exact identity | Specs[].modelCode and Support[].modelCode |
| spec groups | Specs[].fullSpecs[].groupName |
| spec pairs | fullSpecs[].specList[].name/value |
| annual energy | name `Energy Consumption`, sample value `700 kWh/yr` |
| total capacity | name `Total Capacity (cu. ft.)`, sample value `29` |
| spec claim | name `ENERGY STAR® Certified`, sample value `Yes` |
| EnergyGuide metadata | Support[].supports[] where name matches `Energy Guide`, fields name/type/url |

Sample exact target: RF29DB9900QDAA. EnergyGuide URL from its Support record:
`https://images.samsung.com/is/content/samsung/p6pim/us/rf29db9900qdaa/energyguide/us-energyguide-rf29db9900qdaa-550480754.pdf`.
Download spec sheet is a different document and must not be mistaken for EnergyGuide.
Dedicated structured claim flag, title, and rendered badge contracts remain unverified;
absence of a verified flag is UNKNOWN, not false. Commerce is observed in pf_search;
PDP ecom-data mapping is a separate follow-up contract.

## Evidence and tests

Initial request/PDP observation: Actions run 35100922262, commit bf4e18820dadff8288edef2738d6040ab9bc5a09.
It captured all three pages but reported FAIL because a UI click timed out.
Its broad diagnostic artifact was deleted after an unrelated anonymous chat response
was found. Required public product fields were explicitly projected into fixtures.
No chat/IP/cobrowse/license/analytics metadata is committed.

Fixtures: tests/fixtures/refrigerator/pf-page-0/1/2.json and bridge-specs-support.json.
Source projection and identity/pagination assertions: scripts/source_contract.py.
Successful source run: https://github.com/Empty-Bell/RDA/actions/runs/35101696712,
commit 5b4a91c3fb20c7f2cb334e539446bfb290aee498, attempt 1.
Artifact 10448149098, ZIP hash 69cd8ff54d39bca020b5a6906a4f46c841d5efd4c1fe13e8990a73df156c5558.
17 tests, all population pages, sample exact PDP and live EnergyGuide PDF, EPA metadata/sample passed.

The live EnergyGuide PDF returned HTTP 200 / application/pdf, size 92496 bytes,
SHA256 3f0a9d21947c986f9a45c611043bfc67b92bdb75974e77acaea81c89dcce02e9.
PyMuPDF text is whitespace, so embedded text does not satisfy a field quality gate.
Final run used 2x RapidOCR fallback (`EMPTY_EMBEDDED_TEXT`) and preserved raw text.
Label image visually checked: model RF29DB9900**, yearly electricity 700 kWh,
capacity 28.6 Cubic Feet. These are human-checked source observations for this fixture,
not approved normalization/matching rules or a compliance finding.
PDP capacity 29 and label capacity 28.6 differ; a rounding/measurement contract is
required before using capacity as independent identity corroboration.

Run 35101447985 returned pf_search HTTP 403 despite earlier/later access success.
This is a hosted source-access health event, not missing product/document evidence.
The collector now bounds page retries to three attempts; stable hosted access is not established.

Desktop-UA mitigation: scripts/browser_runtime.py preserves actual Linux Chromium
OS/version, replaces HeadlessChrome with Chrome, and fixes en-US desktop viewport.
Source run 35102481369 and runtime run 35102481276 passed after this change.
The source run verifies navigator UA and actual pf_search request UA agree.
Record native/effective UA in artifacts; do not claim the historical 403 root cause
or permanent resolution from these two successful runs.

Contract regression tests: tests/test_source_contract.py (20 tests in total with probe guards).
Final hosted validation: https://github.com/Empty-Bell/RDA/actions/runs/35101976503,
commit 4c0193c06f921af4b38b8d895d78a953a838ff0e, attempt 1, job 104813390799.
20 tests, all four live reconnaissance checks and artifact upload passed.
Artifact 10448527895, size 474900 bytes, ZIP SHA256
35bd70c32cc77e398f507a3701bbc2d7c6cfbdc43449eef19eb552fa46c27d2c.
Raw PDF/render remain in artifact (expires 2026-09-30). Compact observed metadata/text
is versioned in docs/evidence/refrigerator-source-recon.json.

Remaining: other 10 groups; independent rendered badge/structured claim contracts;
PDP title/commerce mapping; full PDF field-quality parser and low-resolution/wildcard
regression corpus; stable hosted-source access; EPA matching/currency semantics.
This closes the bounded refrigerator source reconnaissance, not full Phase 0.
