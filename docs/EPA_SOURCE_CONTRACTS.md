# EPA source contracts — all product-family discovery and bounded query observations

The family notes below are chronological discovery snapshots; their earlier
remaining-UNKNOWN counts are historical, not current coverage. All 11 product
groups now have hosted metadata/generic-sample evidence for nine distinct datasets.
Bounded Samsung literal-brand pagination and official-domain advertisement passed
in run 35165687365, with full source regression 35165687343. See
EPA_QUERY_SOURCE_CONTRACT.md and docs/evidence/epa-query-recon.json for observed
types, markets, UPC omission, update metadata and error/empty-response boundaries.
Per-retail-SKU matching, current certification and cross-version completeness remain
NOT_EVALUATED. Catalog advertisement and a complete brand query never approve D09.

Catalog reachability does not establish a certification match.
Each of 11 families requires dataset ID/endpoint, brand/model/UPC, energy unit,
market/certification status, current snapshot definition, timestamp/hash and fixtures.
Pagination failure or schema drift must never become NO_CURRENT_EPA_CANDIDATE.

Dishwasher q8py-6w3f live metadata and three sample rows passed in hosted run
35103320640. See [DISHWASHER_SOURCE_CONTRACT.md](DISHWASHER_SOURCE_CONTRACT.md).
Observed energy/date fields are annual_energy_use_kwh_year and date_certified;
do not substitute refrigerator field names. The other 9 families remain UNKNOWN.

Washer bghd-e2wd schema/sample passed in hosted run 35104751514. Energy is
annual_energy_use_kwh_year; Date Certified displays on field date_qualified.
Annual water, IMEF and IWF are distinct quantities. Separate all-in-one dataset
9jai-gs6t applicability is not verified; do not force every washer listing SKU into
the standalone dataset. See [WASHER_SOURCE_CONTRACT.md](WASHER_SOURCE_CONTRACT.md).
Other 8 families remain UNKNOWN. Certification matching is NOT_EVALUATED.

TV pd96-rr3d schema/sample passed in run 35105667331. Annual energy is
reported_annual_energy_consumption_kwh, Date Certified is date_qualified. Certification
on-mode power and federal-test on-mode power are distinct W fields. Neither power
field substitutes for annual kWh; missing UPC in individual rows does not establish
a missing certification. See [TV_SOURCE_CONTRACT.md](TV_SOURCE_CONTRACT.md).
Other 7 families remain UNKNOWN. No Samsung model certification lookup performed.

Range m6gi-ng33 (Residential Electric Cooking Products) schema/sample passed in
run 35106676958. Shared Cooktop/Range product_type, total annual energy and oven/
cooking-top low-power component energy are preserved independently. Commercial
electric cooktops nt9t-yxu3 must not substitute. Gas/dual-fuel applicability remains
open. See [RANGE_SOURCE_CONTRACT.md](RANGE_SOURCE_CONTRACT.md).
Other 6 families remain UNKNOWN; certification matching NOT_EVALUATED.

Cooktop independently revalidated m6gi-ng33 schema/sample in hosted run 35107565285.
Sales population includes gas/radiant/induction source URLs; generic EPA sample
does not imply a Samsung gas or electric candidate match. See
[COOKTOP_SOURCE_CONTRACT.md](COOKTOP_SOURCE_CONTRACT.md) and SOURCE_COVERAGE.md.
Other 5 families remain UNKNOWN. No per-SKU certification matching performed.

Clothes Dryer t9u7-4d2j schema/sample verified in hosted run 35109208255.
Fuel type, drum capacity, CEF and estimated annual kWh are distinct raw fields;
combo washer label energy and Samsung raw Energy Factor never substitute for CEF
or dryer annual energy. See [DRYER_SOURCE_CONTRACT.md](DRYER_SOURCE_CONTRACT.md).
Other 4 families remain UNKNOWN. Samsung candidate/currency matching NOT_EVALUATED.

## Refrigerator v0.1

Dataset `p5st-her9`, `ENERGY STAR Certified Residential Refrigerators`, identified
in the official data.energystar.gov catalog in hosted run 35100312790.
Most Efficient (`hgxv-ux9b`) is a separate dataset, not a substitute certification population.

Metadata: `https://data.energystar.gov/api/views/p5st-her9.json`.
Rows: `https://data.energystar.gov/resource/p5st-her9.json`.

Observed official metadata field names:
- pd_id (ENERGY STAR Unique ID, number in metadata; text in JSON row)
- brand_name (text)
- model_number (text)
- additional_model_information (text)
- upc (text)
- annual_energy_use_kwh_yr (number)
- markets (text)
- date_qualified / date_available_on_market (calendar_date)
- energy_star_model_identifier (CB Model Identifier, text)

Do not treat date_qualified alone as active certification status or assume UPC is unique.
Current-snapshot/withdrawal semantics, exact market values, wildcard semantics,
and pagination/query behavior still require explicit contract verification.
Hosted metadata and sample access passed in runs 35101447985 and 35101696712.
rowsUpdatedAt is 1789478931 in the observed snapshot; this is source update metadata,
not a rule defining certification currency. Sample markets: `United States, Canada`.
annual_energy_use_kwh_yr is a numeric string in JSON; preserve unit/period when normalizing.
Sample model `AREF18**` contains repeated wildcards. Preserve them verbatim;
matching semantics are not inferred from the sample. A metadata UPC column can exist
while individual JSON rows omit UPC; missing UPC is not a failed certification match.

Fixtures: epa-metadata.projected.json, epa-sample.projected.json.
Schema tests distinguish dataset access from certification lookup and reject missing
required columns or an empty/error sample without creating a no-candidate conclusion.
Certification matching is NOT_EVALUATED.

Tablet discovery: rxdj-2c88 Certified Computers V9.0 also covers slate/tablets in
the official Computers specification. See TABLET_SOURCE_CONTRACT.md for hosted
metadata and generic sample evidence. Preserve EPA type; Android alone does not
classify a record as Tablet. PDP battery mAh and playback hours are not EPA battery
Wh or TEC kWh. No Tablet/Samsung candidate lookup or current-certification rule exists.

Ventilating Hood discovery: official Certified Ventilating Fans dataset 8dv7-nngq;
see HOOD_SOURCE_CONTRACT.md for URLs, observed fields and type/measurement limitations.
The generic sample includes bathroom/utility fans; no Samsung SKU lookup is implied.

Monitor/Display discovery: qbg3-d468 Certified Displays; see MONITOR_SOURCE_CONTRACT.md.
Product Type, voltage-specific annual monitor energy and mode power are separate.
The generic signage sample can omit monitor annual energy; no per-SKU match implied.

Computer discovery: rxdj-2c88 ENERGY STAR Certified Computers V9.0; see
COMPUTER_SOURCE_CONTRACT.md. Type and exact hardware/OS configuration matter for
later routing/matching. TEC kWh, mode power W, adapter rating W and battery Wh differ.
Android OS in a generic Integrated Desktop sample does not establish Tablet routing.
