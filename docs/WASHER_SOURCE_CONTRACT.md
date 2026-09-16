# Clothes Washer source reconnaissance

Status: RUNNING; Phase 0 only. Certification matching/compliance NOT_EVALUATED.

Official discovery references:
- Samsung listing: https://www.samsung.com/us/laundry/washers/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-clothes-washers
- EPA metadata: https://data.energystar.gov/api/views/bghd-e2wd.json
- EPA sample: https://data.energystar.gov/resource/bghd-e2wd.json?$limit=3
- Separate combo dataset: https://data.energystar.gov/w/9jai-gs6t/im48-wy4k

Runtime uses installed-version desktop Linux Chromium UA, cold hosted Ubuntu 24.04,
bounded retries and no LLM. Category and bridge group identities are observed from
actual page requests. All source variants retain exact SKU and group provenance.
Terminal pagination and unique DOM tile groups must match the observed API total.

EPA schema observed directly from the official metadata: annual_energy_use_kwh_year,
date_qualified (display name Date Certified), integrated_modified_energy_factor_imef,
integrated_water_factor_iwf and annual_water_use_gallons_year. Energy is per year;
annual water must not be compared to dishwasher water per cycle.
Metadata identity/schema will also be revalidated on hosted Ubuntu.

The washer listing may include all-in-one and stacked products. Do not force every
listing SKU into a standalone residential washer certification dataset. Catalog
presence, qualified date and sample availability do not prove active certification.
Combo routing and washer-versus-dryer label selection require source evidence before
matching. No new compliance rule or issue code is introduced in this reconnaissance.
