# Television source reconnaissance

Status: RUNNING. Phase 0 only; certification matching/compliance NOT_EVALUATED.

Official discovery:
- Samsung listing: https://www.samsung.com/us/televisions-home-theater/tvs/all-tvs/
- Federal catalog: https://catalog.data.gov/dataset/energy-star-certified-televisions
- EPA metadata: https://data.energystar.gov/api/views/pd96-rr3d.json
- EPA sample: https://data.energystar.gov/resource/pd96-rr3d.json?$limit=3

Observed EPA metadata identifies ENERGY STAR Certified Televisions, pd96-rr3d.
Separate reported_annual_energy_consumption_kwh (annual energy),
power_consumption_in_on_mode_watts (certification average on-mode power),
reported_on_mode_power_per_the_federal_test_procedure_watts (federal test power),
diagonal_viewable_screen_size_inches and date_qualified (displayed Date Certified).
Power W cannot substitute for annual kWh. Test basis and operating mode must remain
attached to values; multiple power fields are not synonyms.

Samsung category/group/request pagination and PDP spec names must come from the
actual page/network. Screen-size siblings retain exact SKU provenance. Current API
groups must reconcile with terminal pages and distinct rendered card groups.
Sample Specs/Support selects exact modelCode. Preserve original EnergyGuide before
PyMuPDF/OCR extraction. OCR fallback checks empty, short and missing numeric kWh text;
this is extraction health, not a complete field-quality or compliance gate.

Runtime: standard cold ubuntu-24.04 x64, installed-version desktop Chromium UA,
bounded retries, no LLM. All acceptance requires real hosted Actions evidence.
