# EnergyGuide field candidate and provenance contract

Status: bounded field/coordinate reconnaissance PASS; hosted run 35163198471.
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
in text order; increasing the window is not a fix. Actual coordinate fixture verification
then associated US number detection 28 / unit detection 36 with its annual caption,
excluding Canadian 200/307 comparator values in the other column. The proposed
association remains raw evidence, not canonical annual selection.

Geometry uses overlapping caption/number columns, nearby kWh detection and nearest
vertical distance in PDF points. Bounds are extraction heuristics (8 text heights
for caption proximity, 2 heights for numeric/unit gaps), not comparison tolerances.
Keep all proposals and their detection indices. Synthetic unreadable kVVh is not
corrected to kWh. No confidence threshold or wildcard correction is invented.

Intermediate artifacts: original PDF, energyguide-page-1-2x.png,
energyguide-embedded-spans.json, energyguide-ocr-spans.json,
energyguide-field-candidates.json and energyguide-observation.json. Zero numeric
kWh candidates fails extraction health; observing candidates never passes annual
field selection, identity matching or compliance. Field observation health also
requires at least one annual-caption geometry candidate and matching PDF hashes.
The 154-test suite includes actual coordinates for five labels plus source text
fixtures and glyph-error cases. First failed hosted run 35162843284 represents
shipped failing mixed-order tests, not a Samsung source failure. Corrected candidate
run 35162912783 passed all 12 source jobs. Its OCR coordinates/confidences are the
fixture source; no reinterpretation overwrites the original extraction.
Remaining G0 quality work: actual low-resolution regression and wildcard ROI evidence;
full production canonical field selection/corroboration follows approved semantics.

Final ubuntu-24.04 x64 run 35163198471, code commit
9f577eeb38b95cb49e49be6d1f453a1b8709ff82, passed 154 tests and all 12 source jobs.
Five observed labels passed PDF hash, raw numeric and annual-caption geometry
extraction-health checks. Original PDF hashes, raw candidates, geometry proposals,
job IDs and artifact ZIP hashes/expiry are retained in
docs/evidence/energyguide-field-recon.json. Raw artifacts expire 2026-09-30 UTC;
compact evidence does not replace PDF/PNG inputs for future replay.
See energyguide-field-failure-history.json for the initial test implementation failure.
