# FTC/EPA family applicability evidence — 2026-09-17

Phase 0 observations. Hosted authority probe PASS in
[run 35169376748](https://github.com/Empty-Bell/RDA/actions/runs/35169376748), code
b6e6f13c76041d8aa0034d04243060646a0abb65, attempt 1, job 105037485756.
Source access/extraction
PASS is separate from SKU applicability, certification or compliance PASS.
All D01–D12 remain OPEN. No applicability configuration/rule is activated.

## Authorities and dated scope

- **F1: [official eCFR Title 16 version metadata](https://www.ecfr.gov/api/versioner/v1/titles.json).**
  Select Title 16's declared latest issue date; preserve latest amendment and
  up-to-date-as-of dates. The local observation is issue 2026-08-31, amended
  2026-08-29, up to date as of 2026-09-15. Do not represent this as a guarantee
  covering events after that cutoff. Hosted before/after metadata must agree.
- **F2: [Part 305 official XML](https://www.ecfr.gov/api/versioner/v1/full/2026-08-31/title-16.xml?chapter=I&subchapter=C&part=305).**
  Dynamic runtime URL uses F1's issue date, not a fixed production date. Preserve
  wire/decompressed hashes and raw XML before parsing. Extract §§305.2 (definitions),
  305.3 (appliance/electronics descriptions), 305.9 (manufacturer website labels),
  305.13–16 (layout/refrigeration/washer/dishwasher label content), 305.25 (TV labels)
  and 305.27 (catalog/websites), retaining indexed paragraphs and headings.
- **F3: [FTC rule summary](https://www.ftc.gov/legal-library/browse/rules/energy-water-use-labeling-consumer-products-under-energy-policy-conservation-act-energy-labeling)**
  and [manufacturer FAQs](https://www.ftc.gov/business-guidance/resources/energyguide-labeling-faqs-appliance-manufacturers).
  These corroborate the four V1 EnergyGuide groups; the dated FAQ is guidance,
  not a replacement for the current declared eCFR version. A site's commerce
  facts and catalog definition still need evaluation before a website finding.
- **E1: [official In Effect specifications](https://www.energystar.gov/products/spec)**
  and [EPA DCAT](https://data.energystar.gov/data.json). Hosted routing run
  35168707877 already retains the nine specification rows, effective dates,
  PDF links, schemas and Active Specifications advertisement. See
  EPA_ROUTING_SOURCE_CONTRACT.md and docs/evidence/epa-routing-recon.json.
- **E2: [washer criteria](https://www.energystar.gov/products/clothes_washers/key_product_criteria)**
  and [dryer criteria](https://www.energystar.gov/products/clothes_dryers/key_product_criteria).
  Fresh hosted main-content projections exclude footer/script/style text.
- **E3: [Washer 8.1 final specification](https://www.energystar.gov/sites/default/files/ENERGY%20STAR%20Version%208.1%20Clothes%20Washer%20Final%20Specification%20-%20Partner%20Commitments%20and%20Eligibility%20Criteria.pdf),**
  §1.C–D (PDF page 4) defines single-drum all-in-one versus separate stacked drums;
  §2 (PDF page 5) records eligibility/exclusions, including water-cooled all-in-one
  drying and heated-drying functionality. A retail stacked bundle is not thereby
  established as an EPA-defined Laundry Center. These are official source
  observations; individual classification remains D09 work.

## Family evidence matrix

| Retail product group | FTC V1 evidence / location | EPA program and dataset / E1 | Individual boundary still requiring facts or policy |
|---|---|---|---|
| Refrigerator | F2 §305.3(a), §§305.13–14, §305.27(a)(1)(i); F3 | Consumer Refrigeration 5.1 / p5st-her9 | Refrigerator versus refrigerator-freezer, capacity/test basis, model-pattern identity |
| Dishwasher | F2 §305.3(c), §§305.13/16, §305.27(a)(1)(i); F3 | Dishwashers 7.0 / q8py-6w3f | US EnergyGuide versus Canadian EnerGuide regions; capacity classes |
| Clothes Washer | F2 §305.3(d), §§305.13/15, §305.27(a)(1)(i); F3 | Washers 8.1 / bghd-e2wd; combo view 9jai-gs6t | Standalone/all-in-one/Laundry Center; drum/drying definitions and washer label quantity |
| Television | F2 §305.3(h), §305.25, §305.27(a)(1)(i); F3 | Televisions 9.1 / pd96-rr3d | TV tuner definition versus display; model suffixes; annual kWh versus power W |
| Range | V1 EPA-focused; no automatic legal N/A | Electric Cooking 1.0 / m6gi-ng33 | Cooking specification §2, PDF page 5: electric cooking-top component; gas/dual-fuel/oven-only facts |
| Cooktop | V1 EPA-focused; no automatic legal N/A | Electric Cooking 1.0 / m6gi-ng33 | Same §2: standalone conventional electric tops; gas excluded under that specification |
| Clothes Dryer | V1 EPA-focused; combo washer label evidence stays washer-domain | Dryers 1.1 / t9u7-4d2j; E2 combo guidance points to washers | Gas/electric/compact/vented/ventless, separate drying metrics, component/bundle identity |
| Ventilating Hood | V1 EPA-focused; no automatic legal N/A | Ventilating Fans 4.2 / 8dv7-nngq | Fans specification §2, PDF pages 4–5: residential range hoods, configurations and exclusions; zero Samsung rows is not N/A |
| Monitor / Display | V1 EPA-focused; preserve TV/display distinction | Displays 8.0 / qbg3-d468 | Monitor/signage classification; tuner and configuration facts |
| Computer | V1 EPA-focused; no automatic legal N/A | Computers 9.0 / rxdj-2c88 | Notebook definition, configured hardware/OS, Chromebook provenance; operating system alone does not select scope |
| Tablet | V1 EPA-focused; no automatic legal N/A | Computers 9.0 / rxdj-2c88 | Computers §§1–2, PDF pages 6/10–11: Slate/Tablet definition; cellular voice exclusion; Wi-Fi/LTE variants |

The last seven rows express the MASTER_PLAN V1 collection scope; they are not a
legal conclusion that every such product has no FTC obligations. F2's website
label paragraph lists the four FTC V1 groups; parser extraction never turns
nonmembership, missing data or a network failure into a legal exemption.

## Laundry/configuration boundaries

| Observation | Evidence available | What it does not establish |
|---|---|---|
| All-in-one combo | E2/E3; hosted combo-view and parent-filtered identity multisets agree for three Samsung rows | Whole-appliance energy, wildcard expansion or SKU certification |
| Laundry Center | E3 separate stacked drums; new grouped literal Samsung `special_type` queries in both washer/dryer sources | Every retail stacked set is a center; how two component IDs map to a bundle |
| Paired washer/dryer | Existing metadata has paired-availability/model-identifier fields | A paired indicator proves certification of the partner component or canonical combined identity |
| Tablet/Notebook configuration | Existing selected-config PDP identity plus E1 program definitions | All configurations inherit certification from a parent/gallery page |
| Ducted/recirculating hood | Existing PDP configuration facts and Fans §2 source scope | Test-basis equivalence or every available installation configuration is supported |

Grouped query counts are dated source observations, not listing population counts,
complete certification coverage, independent corroboration or atomic snapshots.
Empty/unspecified special_type remains raw; do not coerce it to standalone/N/A.

## Verification

`applicability-recon.yml` uses pinned Actions, Python 3.12.14 and ubuntu-24.04 x64,
with no pip install/browser/OCR/LLM. It verifies authority contracts, raw XML,
declared version stability, public EPA criteria main text and bounded type queries.
An 8 MiB bound applies separately to compressed and decompressed bytes; errors
retain FAIL and diagnostics. XML DTD/entities, malformed/missing/duplicate sections,
missing dates, duplicate main and footer/script-only titles are rejected.

The local eCFR full XML request without Accept-Encoding returned HTTP 406,
explicitly requiring response compression. Gzip negotiation resolved it without
TLS bypass. This is a documented API requirement, not evidence of a UA-related fix.
Sanitized authority fixtures and original source hashes are recorded in
docs/evidence/applicability-fixture-manifest.json. Raw artifacts retain 14 days.

Next: G0 contract closure checklist and fixture coverage review; explicitly assign
remaining semantic decisions to their due phase. Full G0 is not promoted here.

## Hosted results

Twelve authority contract tests passed. The declared eCFR dates match F1 above
and were stable before/after XML extraction. Nine required sections were extracted
from the actual Part 305 XML; raw bytes, wire/body hashes and normalized section
paragraphs remain in the artifact. The cutoff is 2026-09-15, not a claim of live
legal completeness through the observation date.

Both washer and dryer grouped Samsung queries expose three all-in-one rows and
seven Laundry Center rows. Unspecified special_type has 56 washer and 94 dryer
rows and remains unspecified. These historical counts are not production constants;
equal center counts do not prove equal identity sets or a bundle/component join.
No current-certification, market, wildcard or SKU applicability rule was approved.

Fresh criteria main-content projections and authority/query/ZIP hashes are in
docs/evidence/applicability-recon.json. The independent
[fixture integrity run](https://github.com/Empty-Bell/RDA/actions/runs/35169376791)
passed all 99 references, including three new authority fixtures, against actual
Ubuntu checkout bytes. No package/browser/OCR/LLM installation or call was needed.
