# EPA source contracts — refrigerator dataset identified; other families UNKNOWN

Catalog reachability does not establish a certification match.
Each of 11 families requires dataset ID/endpoint, brand/model/UPC, energy unit,
market/certification status, current snapshot definition, timestamp/hash and fixtures.
Pagination failure or schema drift must never become NO_CURRENT_EPA_CANDIDATE.

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
