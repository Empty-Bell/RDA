# Computer EPA-focused source reconnaissance

Status: bounded hosted reconnaissance PASS; Phase 0 overall RUNNING;
certification/compliance NOT_EVALUATED.

Official sources:
- Samsung https://www.samsung.com/us/galaxybooks/ All Galaxy Books redirects from
  /us/computing/galaxy-books/all-galaxy-books/ to
  https://www.samsung.com/us/computers/galaxy-book/. Its All tab uses the same URL.
- Separate Galaxy Chromebook tab https://www.samsung.com/us/computers/chromebook/.
  It must be collected separately; Galaxy Book All alone is not all consumer computers.
- Catalog https://catalog.data.gov/dataset/energy-star-certified-computers-v9-0
- Metadata https://data.energystar.gov/api/views/rxdj-2c88.json
- Generic sample https://data.energystar.gov/resource/rxdj-2c88.json?$limit=3

EPA official identity is ENERGY STAR Certified Computers V9.0, rxdj-2c88.
Preserve type, operating_system_name, system_memory_ram_gb, mode watts,
total_battery_capacity_watt_hours, external_power_supply_rated_power_w,
tec_of_model_kwh and date_certified. Battery storage Wh, rated adapter W,
measured mode W, model TEC kWh and TEC certification allowance/limit are distinct.
Metadata labels TEC of Model (kWh); period/test basis must be verified before
comparison or annual normalization. Do not infer certification currency from date.

Static search HTML placeholders/no-results are not a live zero population.
Accept browser-observed terminal pf_search pages only after unique API groups
reconcile with rendered product-card groups. Preserve exact SKU configurations;
same product name or family does not establish the same CPU/RAM/OS configuration.
Consumer listing coverage does not prove exhaustive business/support catalog coverage.
Purchase configurators use selected [data-modelcode][aria-checked=true] controls and
the visible Continue button's data-modelcode as the current SKU surface. All selected
controls must match the target; do not click Continue. A known Specs-only endpoint
pattern uses the current observed ecom-data group_id and modelCode, without fixed IDs:
/us/gapi/v1/bridge/cacheable/bridge-data?data_type=Specs&store_type=B2C&group_id=...&modelCode=...&version=v2.
The response is a top-level array containing several modelCode/fullSpecs records;
select exactly one target record, never the first array record. Preserve only modelCode,
groupName and name/value spec pairs. Specs-only evidence has document_collection_status
NOT_EVALUATED, energyguide_metadata_count null; absent Support is not zero documents.
Other product groups retain their existing strict Specs/Support contract.
No per-SKU EPA lookup occurs.
EnergyGuide validation OUT_OF_RECON_SCOPE under EPA-only discovery is not a legal finding.

Cold standard ubuntu-24.04 x64, actual-version desktop Chromium UA, en-US,
no runtime LLM. Initial Galaxy Book run 35111568246: 11 API groups = 11 rendered
groups, 23 exact SKUs. category_code 03010000, taxonomy_code 03010100, requestCount 22,
terminal first page. Chromebook observation run 35113871784: 1 group / 1 SKU.
Counts are snapshot observations, not production constants.

Galaxy Book sample NP960UJH-XG7US passed the revised contract in run 35113694951,
job 104853617705, commit 3474616: selected SKU + visible purchase control + exact
Specs array. Battery Capacity (Typical, Wh) 80.20; AC Adapter 140W USB Type-C Adapter;
CPU Intel Core Ultra 9 386H; GPU RTX 5070; RAM 64 GB; storage 2 TB.
No annual PDP energy, ENERGY STAR structured claim or Support absence is inferred.
Several records returned by one Specs API do not mean several individual PDP visits.

EPA has 68 public columns and 3 generic samples. First sample ELO Integrated Desktop,
Android OS, adapter 65.0 W, short idle 7.3 W, sleep 3.0 W, model TEC 34.0 kWh.
OS Android alone does not establish Tablet classification. Missing battery value in a
desktop sample is not zero capacity or a failed candidate match.

Initial fixed-delay/body-text checks failed on lazy purchase summary; viewport jumps
were inconsistent. Selected current controls and visible purchase SKU plus exact backend
Specs provide independently observed identity. No URL-only relaxation is used.
Earlier failures remain versioned in computer-source-failure-history.json.
Run 35113116324 also included an implementation pagination regression (undefined target)
from a misplaced scroll edit; corrected in 3474616, not attributed to Samsung source.
Chromebook sample XE550XGA-KC1US passed run 35114137145, job 104855739869:
Chrome OS, Intel Core 3 100U, 8 GB RAM, 256 GB storage, 68.0 Wh battery,
45 W USB Type-C Adapter. It uses the same selected SKU / Specs-only contract.
Both source legs and all nine earlier product groups succeeded in that run
(11 jobs for 10 product groups; Chromebook is a Computer source leg).
The disjoint observed listing union is 24 exact SKUs / 12 source groups, not 23.
Raw API fields remain verbatim; no battery/adapter-to-annual-energy conversion.
Fixtures and their source-run SHA256 manifest are versioned under tests/fixtures/computer
and docs/evidence/computer-fixture-manifest.json.

Final acceptance: run https://github.com/Empty-Bell/RDA/actions/runs/35114575198,
commit deabaff76e980ba33c97e54a3fd4ad31ba60532f. 103 tests and all four live checks
for each Computer source leg passed; all 11 source jobs for 10 product groups succeeded
on cold standard ubuntu-24.04 runners. Current listing union recomputed as 24 exact SKUs.
Galaxy Book job 104856607424, artifact 10455345030, 18506 bytes, ZIP SHA256
b82dd71da3fbd9b3f17636555c615c988f34b97742489661ecb0a0b9c88e7cc2.
Chromebook job 104856607323, artifact 10455330019, 13296 bytes, ZIP SHA256
7072fffac0565eed276a77ecf10c397675b69a502e042be242d8225c7102409d.
Compact final evidence: docs/evidence/computer-source-recon.json. Raw artifacts expire
2026-09-30 UTC; exact expiry timestamps are in evidence. Successful bounded snapshots
do not establish permanent access stability, complete per-SKU collection, EPA matching
or full G0 acceptance.
