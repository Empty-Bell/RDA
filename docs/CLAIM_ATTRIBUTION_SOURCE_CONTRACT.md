# Current-product badge attribution and nested flag discovery

Status: initial hosted discovery PASS; final scoped regression pending.
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
