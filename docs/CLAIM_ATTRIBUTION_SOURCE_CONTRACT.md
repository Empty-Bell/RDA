# Current-product badge attribution and nested flag discovery

Status: bounded hosted discovery and final scoped regression PASS.
Phase 0 RUNNING; certification and claim consistency NOT_EVALUATED.

Observed PDP badge asset: image-us.samsung.com/us/b2c_pf/badge/
energy-star-logo-pdp-m@2x.png. A visible IMG candidate must have the observed badge
path, one primary surface, one Product JSON-LD record with all nonempty SKU/MPN
identifiers agreeing with the target, and the existing PDP identity gate already
passed. Only these observed surfaces are supported:
- Gallery_energyStarContainer__ inside Gallery_outerContainer__ (CSS module prefix;
  deployment hash not fixed), with exactly one gallery root.
- q6b6RelationContainer on the purchase configurator, exactly one relation root.

This records a logo on the currently identified primary product surface. It is not
EPA certification or proof for every family/color/storage variant. Generic marketing
images, footer candidates, unrelated/multiple JSON-LD products and duplicate surfaces
remain unattributed. Missing/unsupported surface is NOT_EVALUATED, never false.

Structured discovery projects scalar ENERGY STAR key fields plus their JSON path
and nearest explicit modelCode/modelcode/model_code/sku identifiers from observed
public bridge-data/ecom-data responses, manual Specs-only requests and public
script#__NEXT_DATA__ if present. Child product identifiers replace parent identity;
related/recommended/accessory/variant/bundle/alternative branches reset inherited
identity until an explicit product identifier is encountered. Unbound/conflicting
identifiers cannot supply a current-SKU flag. Raw values are not normalized to truth.

Exclude observed non-product data_type Footer, GNB, Offer, ExchangeDevices,
Promotions, PricingPromotion and EppHeader from this product-field survey. The
initial Tablet Offer/ExchangeDevices probe was truncated and retained as diagnostic
fixture evidence, not silently reclassified as complete. No full payload is stored.
Account/chat/analytics/license/auth/token/session/cookie/customer/email branches
are excluded. Bound traversal at 20000 nodes, depth 16 and approximately 100 fields;
truncation is recorded, not converted into field absence. Access/JSON errors fail
observation health. No observed matching flag remains NOT_EVALUATED even when the
bounded projection completes; other unobserved interfaces are not proven absent.

Initial run https://github.com/Empty-Bell/RDA/actions/runs/35161180701,
commit c66462cce651d4cf038cb4a83dc3e6362280a5b2: all 12 source jobs succeeded.
RF29DB9900QDAA gallery and SM-X930NZAAXAR configurator relation are preserved in two
product-only fixture projections and their source-run/SHA256 manifest. Synthetic
tests cover identity conflict, related products, footer/marketing assets, duplicate
surfaces, nested raw flags, private branches and traversal limits.

Next common G0 task after final acceptance: EnergyGuide field-quality/source parser
contract. Broader unobserved flags remain explicitly unknown; no consistency or
certification rules are implemented by this discovery.

Intermediate acceptance: https://github.com/Empty-Bell/RDA/actions/runs/35161424880,
commit fc7aa0441944d3273cd636a4da008ceb8be711fa. All 12 source jobs for 11 product
groups passed the 138-test suite and live source/claim observation gates. Original
public artifacts, expiry, job IDs and ZIP SHA256 are recorded in
the recorded source artifacts. Scope-complete projection is not a
global claim-absence finding or full per-SKU coverage. G0 remains NOT_EVALUATED.

The intermediate full NEXT_DATA survey found energyStarFlag on all 12 primary
target records but was truncated on Computer/Chromebook/Tablet unrelated page props.
The known product path is now a strict parser contract:
script#__NEXT_DATA__ -> props.pageProps.productData.products[].energyStarFlag.
Read only that array, project explicit product identifiers plus field-presence and
raw scalar value, and require one exact target record at interpretation. Missing
path/empty array/identifier/scalar schema drift is extraction failure; missing flag
is separately observed, not coerced to N. Never select the first record by position.
No whole-page traversal or private/trade-in/pricing payload retention is needed.

Narrow parser run https://github.com/Empty-Bell/RDA/actions/runs/35161814700,
commit 836ab92d5da05d455684679f36c394effd7df9a2: all 12 source jobs and 141 tests
passed. Computer and TV projections provide actual positive/negative fixtures and
source-run/SHA256 manifest. NP960UJH-XG7US is array index 10, raw Y; MRN75R95HAFXZA
is index 6, raw N. Positions are historical fixture observations, not constants.
These raw Samsung flags and the logo may share an upstream data source: do not
count them as independent proof of EPA certification. Keep source provenance and
observation values separate from consistency/matching rules.

Final acceptance: https://github.com/Empty-Bell/RDA/actions/runs/35162114501,
commit a39c9e3914c13a7554ab1954c3edd18827b3fea3. 143 tests and all 12 source
jobs succeeded. All primary samples had one exact inline raw flag and scope-complete
product projections; no remaining whole-page traversal truncation. Eight source legs
had current-product logo attribution (refrigerator, dishwasher, washer, dryer, range,
Galaxy Book, Chromebook, Tablet); TV/cooktop/hood/monitor primary samples stayed
unattributed with no observed logo candidates. Flag raw Y/N values remain separate
from rendered/spec claims and EPA. Compact final evidence is claim-attribution-recon.json;
the intermediate broader/truncated survey is retained in claim-attribution-discovery.json.
Both record observed jobs, artifacts, expiry and ZIP hashes. Full per-SKU collection,
normalized commerce and certification/consistency rules remain downstream.
