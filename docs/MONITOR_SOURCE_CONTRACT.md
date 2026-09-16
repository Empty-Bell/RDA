# Monitor / Display EPA-focused source reconnaissance

Status: bounded hosted reconnaissance PASS; Phase 0 overall RUNNING.
Compliance/certification matching NOT_EVALUATED.

Official sources:
- Samsung marketing https://www.samsung.com/us/monitors/ links Shop All Monitors
  via the historical computing path to https://www.samsung.com/us/monitors/all-monitors/.
- Catalog https://catalog.data.gov/dataset/energy-star-certified-displays
- Metadata https://data.energystar.gov/api/views/qbg3-d468.json
- Generic sample https://data.energystar.gov/resource/qbg3-d468.json?$limit=3

Static search HTML contains unmounted placeholder tiles and no-results text;
neither establishes live population. Accept browser-observed pf_search terminal pages
only after unique API groups reconcile with rendered product card groups.

EPA qbg3-d468 is ENERGY STAR Certified Displays. Preserve display_type (Product Type),
screen_size_inches, on_mode_power_watts, sleep_mode_power_watts, off_mode_power_watts,
monitor_total_energy and date_certified. Metadata names monitor_total_energy as
Monitor Total Energy Consumption at 115 Volts (kWh/yr). It is distinct from mode power W,
maximum_total_energy certification limit and maximum_power_delivery_w USB-C delivery.
Preserve voltage, period and test basis before comparison; no annual kWh from PDP watts.
Smart TV apps do not by themselves establish TV dataset applicability.

Exact Specs/Support record selects sample PDP. ENERGY STAR claim raw source text
does not become a structured certification verdict. EnergyGuide is OUT_OF_RECON_SCOPE
under the master plan's EPA-only discovery scope, not a legal non-applicability finding.
Generic EPA samples are not per-SKU candidate lookups. Current certification, product
type routing and measurement comparability remain open in DECISIONS.md.

Runtime: cold standard ubuntu-24.04 x64, installed-version desktop Chromium UA,
en-US, no runtime LLM. Initial hosted observation run 35110739052, job 104843455715,
commit 87cd10d passed all four checks; all nine family jobs succeeded.
56 API groups = 56 rendered groups; 76 exact SKUs. Actual category_code 07010000,
no taxonomy_code in the request; offsets 0/21/45 and requestCount 21/24/24.
Do not impose another family's taxonomy or fixed population size on this source.

Sample LS40H850TANXZA: Screen Size (Class) 40; two Active Display Size (HxV) raw
values 36.5 x 15.4 in and 926.8 x 391.0 mm; Resolution WUHD (5120 x 2160).
Power Consumption (Max) 340 W; Thunderbolt charging power 140 W and 15 W;
Power Supply AC 100 - 240 V. Class size, dimensions, pixels and capacity are distinct.
Energy Saving Solution Yes is not an ENERGY STAR certification claim.
No annual PDP energy is inferred; EnergyGuide metadata count 0 is not a finding.

EPA observed 44 columns and three generic samples. First sample Acer
ACER ALTOS EZBA65 is Signage Display, on/sleep/off power 131.04/0.45/0.00 W;
monitor_total_energy is absent in that row despite the metadata column being present.
Its absence is not zero energy or no-candidate. No Samsung SKU lookup occurred.
Nine monitor fixture tests reject partial pagination, wrong dataset, missing type
schema and empty EPA samples, and preserve consumption/charging/size distinctions.
Fixtures originate from the initial hosted run; provenance and SHA256 are recorded in
docs/evidence/monitor-fixture-manifest.json. Compact final evidence is versioned in
docs/evidence/monitor-source-recon.json; raw artifacts expire after 14 days.

Final acceptance: run 35111109416, monitor job 104844741738, commit
eb170dfcf1f4ffd9b4167b916e469cee2023935d. 88 tests and all four live monitor checks
passed; all nine family jobs succeeded on cold standard ubuntu-24.04 runners.
Artifact 10452317500, 24125 bytes, ZIP SHA256
29822e97d168577cd3881dca13d90b72eb6e4edf007f8fdca4886c790cd4fc0d.
This accepts the bounded observed snapshot, not permanent source stability or full G0.
