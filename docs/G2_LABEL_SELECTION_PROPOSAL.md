# G2 label-field selection proposal

## Current adopted numeric selection contract

The initial manual PDF review was a one-time validation exercise for the source
selection rules. Normal future runs do not require a person to review every
label. The current automatic annual-energy rule requires one annual-use caption,
one geometry proposal, and exactly one explicit kWh candidate whose value equals
that proposal. Other nearby OCR numbers, such as cost-range endpoints, do not
block selection when they do not match the caption-linked proposal. The capacity
rule requires exactly one complete `Capacity: <number> Cubic Feet` descriptor;
boilerplate text containing the word capacity is ignored.

Both automatic rules retain the current PDF SHA-256, candidate text and layout
coordinates. Missing, conflicting or structurally invalid candidates remain
NOT_OBSERVED. A saved visual review can select an exception only when its exact
SKU and PDF hash match the current collection. The sole current numeric exception
is the preserved OCR text `Capacity: 28.8 Gubic Feet`: the rendered source visibly
shows `Cubic Feet`, and its hash-bound review records the observed and reviewed
strings separately. No general spelling correction is enabled.

Offline replay against full refrigerator artifact 10620777089 selects annual
energy and capacity for 75/75 exact SKUs across all 58 byte-distinct PDFs. This
completes numeric source-field selection, not PDP comparison or product
compliance. The two RF90F documents that explicitly list two model patterns
remain model-identity exceptions; D01 comparison tolerance and the final
EnergyGuide assessment rule are still separate decisions.

Historical status at proposal time: conservative fixture contract adopted; review-bound annual-energy
selection enabled after saved-corpus replay and hosted verification. Capacity/model
selectors and compliance rules remain disabled. Historical proposal evidence and
initial checkpoints below describe the state when the proposal was written.
Scope: refrigerator field extraction only. D01 comparison tolerance, D07 OCR
correction/corroboration and D09 wildcard identity remain OPEN.

## Evidence reviewed

Committed refrigerator text/layout fixtures retain 700 kWh, Model RF29DB9900**,
and Capacity: 28.6 Cubic Feet. The annual number/unit detections are 21/22 and
the annual caption is detection 23, on page 0. Source PDF hash is
3f0a9d21947c986f9a45c611043bfc67b92bdb75974e77acaea81c89dcce02e9.
The dishwasher mixed-region fixture demonstrates why reading order and nearest
distance alone cannot select a value. Existing geometry proposals remain candidates.

Expanded hosted collection run 35176346751 succeeded, but its individual candidate
files have not been independently downloaded/reviewed for this proposal. Its job
success establishes collection health, not the correctness of selected fields.
Before activation, replay this proposal against that saved corpus and preserve
original PDF, OCR image/spans, candidate files and review annotations.

## Proposed selection contract

| Field | Required evidence | Ambiguous outcome |
|---|---|---|
| Annual consumption | Explicit numeric kWh, annual electricity-use caption, same page and verified label panel; exactly one compatible number/unit/caption association | Retain all candidates; no canonical VALUE |
| Capacity | Explicit capacity descriptor and cubic-foot unit in the same label panel; exactly one compatible value | Retain raw lines; no canonical VALUE |
| Model | Explicit Model descriptor and associated token/region | Preserve raw token including every wildcard; no SKU match or correction |
| Document | Exact-SKU Support provenance plus one eligible document/panel; multiple PDFs require explicit review | Preserve every PDF; no automatic winner |

US panel attribution must be explicit where multiple regions occur. Page 0 OCR
does not establish coverage of other pages. A single first-page candidate cannot
win while relevant pages/panels are unreviewed. Geometry bounds are parser
heuristics; they are not acceptance tolerances. Nearest distance, highest OCR
confidence, filename and URL do not independently satisfy selection requirements.

Text order and geometry derived from the same OCR detections are correlated views,
not independent corroboration. Agreement between repeated OCR runs alone does
not approve OCR correction. Conflicting embedded-text/OCR candidates require
review; neither channel silently overwrites the other. A review must reference
the original PDF hash, page, region, detections and reviewer annotation.

Selected annual consumption records the source caption and kWh/year semantic
context without deriving consumption from cost or power. Selected capacity keeps
its source value/unit; 28.6 label versus 29 PDP is not an identity failure or finding.
Raw model RF29DB9900** remains raw and unmatched. No fuzzy wildcard expansion,
character replacement, rounding, tolerance or severity is proposed here.

Collection errors remain ERROR/failed pipeline; missing and ambiguous selection
remain distinct reasons for unavailable canonical observations. No review state
is treated as PASS or as a regulatory finding. Implementation must fit the approved
observation schema without inventing a compliance issue code.

## Activation verification

1. Replay saved expanded refrigerator PDFs/candidates without another live crawl.
2. Annotate expected annual/capacity/model regions against rendered originals.
3. Include mixed panels, multiple documents/pages, conflicting channels, missing
   units/captions, tariff/cost numbers, unreadable glyphs and wildcard examples.
4. Verify same-run/SKU/PDF-hash and detection references; mutate each link to prove
   rejection. Preserve ambiguity rather than choosing a nearest candidate.
5. Run fixture selector contracts on hosted Ubuntu 24.04, Python 3.11 and 3.12.
   Acceptance requires zero unintended selection and explicit unresolved cases;
   current collection success alone does not close G2.

Approval requested: adopt this conservative field-selection contract for a
fixture-only selector implementation. Activation remains dependent on saved-corpus
review and hosted verification. D01/D07/D09 decisions are not approved by this scope.

Fixture implementation checkpoint PASS: run 35177064002 at 8e03ee7 passed 14
offline contracts on Ubuntu-hosted Python 3.11 and 3.12. The selector accepts the
unique refrigerator 700 kWh candidate and rejects multiplicity, text/layout
disagreement and PDF provenance mismatch. It remains disconnected from live
canonical EnergyGuide facts until the saved expanded corpus is reviewed.
