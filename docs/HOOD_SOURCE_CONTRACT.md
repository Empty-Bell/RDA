# Ventilating Hood EPA-focused source reconnaissance

Status: bounded hosted reconnaissance PASS, including final fixture regression.
Phase 0 overall RUNNING. Certification matching/compliance NOT_EVALUATED.

Official sources:
- Samsung listing: https://www.samsung.com/us/cooking-appliances/range-hoods/
- Catalog: https://catalog.data.gov/dataset/energy-star-certified-ventilating-fans
- EPA metadata: https://data.energystar.gov/api/views/8dv7-nngq.json
- EPA sample: https://data.energystar.gov/resource/8dv7-nngq.json?$limit=3

The marketing page's All Hoods link redirects to a mixed cooking-appliance listing;
its Range Hoods link independently identifies the dedicated listing used here.
Do not treat the mixed listing as a hood-only population or infer zero products from
unmounted web-search HTML. Actual population is accepted from browser pf_search and
terminal pages reconciled with unique rendered source groups.

EPA 8dv7-nngq is Certified Ventilating Fans, not a hood-only dataset. Preserve unit_type,
airflow_1_cfm, efficacy_1_cfm_w, sound_level_sones and date_qualified. Multi-speed values
retain their numbered provenance. Lighting total_input_power_watts and luminaire
efficacy are not fan power or airflow efficiency. Bathroom/utility test pressure fields
must not substitute for hood fields. Type/applicability/current matching remain open.

Exact Specs/Support record selects sample PDP. EnergyGuide validation is OUT_OF_RECON_SCOPE
in this EPA-only task. Standard cold hosted Ubuntu 24.04, desktop actual-version Chromium
UA, no runtime LLM. See SOURCE_COVERAGE.md for population versus sample verification.

Initial observation run 35109754946, hood job 104840078593, commit fdfe23f;
all eight family jobs succeeded. API and rendered population both contain 6 groups,
16 exact SKUs. Two visible representative links are not the population count.
Observed pf_search category_code 08080000, taxonomy_code 08080400, requestCount 15,
terminal first page; these observations are not fixed production population constants.
Sample NK30CB700WCGAA has exact Specs/Support, bridge group_id 572573 (a different
namespace from listing group IDs). Raw hood fields: Wall Mount Chimney;
Exterior & Recirculating Capable; 390-630 CFM; 50 dBA (1.0 sones); 210W.
No annual-energy or volume-capacity value is inferred from these fields.
EnergyGuide metadata count 0 is not an applicability or compliance conclusion.

EPA metadata has 42 columns; three generic rows validate access/schema only.
First row ACIQ AEP110 is Bathroom/Utility Room, airflow_1_cfm 110,
efficacy_1_cfm_w 4.2 and sound_level_sones 0.9. This is not a Samsung hood lookup.
Tests preserve raw metrics and reject incomplete listing/schema/empty EPA samples.
Sanitized fixtures originate from the initial run; their hashes and final acceptance
are recorded in docs/evidence/hood-fixture-manifest.json and hood-source-recon.json.
Raw artifact retention is 14 days; compact evidence is versioned in git.

Final acceptance: run 35110234760, job 104841727946, commit
a5b4494b39fed2992aa7503d6e4d673a749e06d5. 79 tests and all four hood source checks
passed on a cold standard ubuntu-24.04 runner; all eight family jobs succeeded.
Artifact 10452375797, 11510 bytes, ZIP SHA256
28ae71ff42692a2898d76216561625698d1330d7f3954acfe429e6fde2d8432a.
This verifies the observed bounded snapshot, not permanent source availability.
