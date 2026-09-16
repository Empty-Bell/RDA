# Dishwasher source reconnaissance

Status: RUNNING. Phase 0 only; certification matching and compliance NOT_EVALUATED.

Discovery references:
- Samsung official listing: https://www.samsung.com/us/dishwashers/all-dishwashers/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-dishwashers
- Official certified dataset: https://data.energystar.gov/w/q8py-6w3f/im48-wy4k
- Most Efficient dishwasher dataset is separate (butk-3ni4); never substitute it.

Hosted checks use the same installed-version desktop Linux Chromium UA as refrigerators.
The category code and bridge request group ID must come from actual page requests.
No request identity is derived from the refrigerator source. Current population is
accepted only if terminal pagination, API groups and unique rendered tile groups reconcile.

Exact PDP Specs and Support records are selected by modelCode. All observed spec
name/value pairs are preserved because refrigerator-specific capacity names cannot
define dishwasher capacity or annual-energy contracts. Original PDF and extraction
text remain in artifacts; automated field parser quality is NOT_EVALUATED.

EPA metadata must identify q8py-6w3f by ID and certified residential dishwasher name.
Schema checks preserve numeric strings and verify brand/model/unique ID, annual
energy, markets and qualified-date columns. Sample availability does not define a
current certification or support any Samsung model match.

Acceptance evidence and sanitized fixture regression tests will be recorded after
the live hosted observations complete. Full Phase 0 remains RUNNING.
