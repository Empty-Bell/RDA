# EnergyGuide field candidate and provenance contract

Status: candidate extraction implemented; hosted coordinate observation pending.
Phase 0 RUNNING; annual field selection, identity matching and compliance NOT_EVALUATED.

Preserve original PDF SHA256 and page count; render first page at 2x. Extract
PyMuPDF text blocks with page/PDF-space bounding rectangles. When numeric kWh is
unavailable in embedded text, preserve that text and run RapidOCR on page 1 at 2x,
retaining every detection's text, confidence and quadrilateral divided by render
scale into PDF coordinates. A first-page sample does not establish whole-document
OCR coverage. Embedded extraction and OCR are separate channels, not overwrites.

Text parser outputs numeric kWh candidates with original line indices, raw context
and unit-association method; standalone numeric detections and annual caption
lines are also retained. Only adjacent or bounded-nearby unit detections generate
order-based candidates. Context tags indicate co-occurrence, not selected annual
values or geometric field ownership. Preserve repeated numbers and US/Canadian
panels; do not deduplicate them into one accepted annual value. Tariff cents per
kWh and currency amounts are not consumption candidates.

Preserve model-like tokens (including wildcard glyphs) and raw capacity lines.
Part numbers can also be model-like; tokens are candidates, not proven model IDs.
Never correct OCR wildcard multiplicity, fuzzy characters, or match a label to SKU
from filename/URL alone. Comparison tolerances/capacity identity rules remain D01/D07.
No new issue code or compliance engine is implemented.

Actual fixtures: refrigerator 700 kWh / RF29DB9900** / 28.6 cubic feet;
washer combo 103 kWh; TV 390 kWh; dishwasher US/Canadian 225 with 200/307 reference
numbers; standalone washer partial embedded text omits numeric energy and requires
OCR. Source run 35162114501 and source SHA256 manifest are recorded. Initial test
expectation of selecting US dishwasher 225 from reading order failed: numeric line
28 and unit line 36 are interleaved with Canadian panel. This remains unresolved
until page-coordinate association is verified; increasing the window is not a fix.

Intermediate artifacts: original PDF, energyguide-page-1-2x.png,
energyguide-embedded-spans.json, energyguide-ocr-spans.json,
energyguide-field-candidates.json and energyguide-observation.json. Zero numeric
kWh candidates fails extraction health; observing candidates never passes annual
field selection, identity matching or compliance. Remaining work: geometric field
association / panel context, low-resolution regression and wildcard ROI evidence.
