# EnergyGuide degradation and model-like ROI probe

Status: hosted discovery PASS in run 35164234556; final regression pending.
Phase 0 remains RUNNING.

This bounded probe reuses each freshly observed original PDF and matching SHA256.
Render page 1 at 36 and 72 DPI; these are controlled degradations of actual public
labels, not proof that naturally low-resolution source labels have been collected.
Keep original PDFs and existing 144-DPI full-page OCR independently. Do not replace
the baseline with an enlarged or degraded interpretation.

Propose model-like regions from baseline detections, including part numbers and
Canadian repeat tokens. Their presence is not validated label/model identity.
Expand each box by one text height, clamp to the page, render at 216 DPI. At most
eight regions are permitted; exceeding the bound fails rather than truncating.
A label without baseline model-like detections has ROI status NOT_OBSERVED; do not
claim exhaustive model-region discovery or introduce filename-based fallback.

Each image retains original PDF hash, PNG hash, page, scale, clip, actual pixel
origin and dimensions. Preserve raw OCR text/boxes/confidence before interpretation.
ROI OCR quadrilaterals are mapped back to PDF space using actual pixel origin
to retain clipping-rounding provenance. Detection-array disagreement fails.

Zero detections at degraded resolution is NO_TEXT_OBSERVED. Missing energy/unit,
model-like token loss and wildcard differences remain observations, never corrected
characters, model matching, discrepancy findings or certification decisions.
Probe PASS means execution and evidence preservation only. Any operational error
saves FAIL and raises, so the Actions job cannot pass because a parser failed.

Intermediate artifacts are quality/{variant}.png, *-render.json, *-raw.json,
*-spans.json, *-observation.json, model-regions.json and summary.json beside each
original label. Artifact upload runs even after job failure. Replay requires the
original PDF/PNG binaries, not just compact checked-in projections.

Hosted evidence must precede acceptance. Actual OCR regression fixtures will retain
source SHA256 and observation provenance without claiming canonical annual fields,
wildcard correction or SKU identity. D01/D07/D09 semantics remain undecided.

Discovery run 35164234556, commit 93a0b7f8c25819ef4eb221cb28bf5190472ab3f3,
passed 159 tests and all 12 source jobs. Five actual labels yielded 20 probe
variants (10 low-DPI pages and 10 model-like ROIs). Source hashes and fixture hashes
are retained in docs/evidence/energyguide-quality-fixture-manifest.json.

Observed 36-DPI refrigerator RF290B9900 differs from baseline RF29DB9900**;
72-DPI dishwasher has both DW90F8**0** and DW90F8**0*** across the two panels.
216-DPI US and Canadian model ROIs repeat DW90F8**0***. Washer 72-DPI part-number
DC58-04582A-00 differs from ROI DC68-04592A-00. Part numbers remain candidates,
not product model identity. At 36 DPI none of the five samples produces an annual
caption layout proposal, despite some numeric text surviving. These observations
are explicit regression fixtures, not silently corrected parser errors.

Compare raw candidate sets with the independent baseline (or source ROI detection).
SAME_RAW_CANDIDATE_SET means string repetition only; it does not establish accuracy,
source authenticity or identity. DIFFERENT_RAW_CANDIDATE_SET preserves uncertainty.
All source detections, including repeated candidates, remain available separately.

Visual review covered refrigerator/dishwasher model ROIs and the degraded TV page;
ROI padding retains neighboring caption/capacity context. Original full-page renders
remain separate. Naturally low-resolution PDFs, unseen model-region discovery and
approved corroboration/confidence semantics remain outside this bounded corpus.
