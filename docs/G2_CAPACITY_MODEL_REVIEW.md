# Capacity and model boundary review

Review scope: the five distinct preserved PDF hashes covering nine additional
refrigerator labels from hosted run 35176346751. No new live crawl is needed.
The OCR-input 2x render, original OCR descriptors and detection coordinates were
reviewed together. Sanitized projections are in
`docs/evidence/g2-capacity-model-review.json`; visual transcriptions are review
annotations, never replacements for OCR text or independently corroborated facts.

| Label group | Raw OCR model | Visible model | Visible capacity (Cubic Feet) |
|---|---|---|---|
| RF18A5101 | RF18A5101 | RF18A5101** | 17.5 |
| RF22A4111 | RF22A4111 with a trailing left double quotation mark | RF22A4111** | 22.1 |
| RF22A4221 | RF22A4221** | RF22A4221** | 22.0 |
| RF23BB8600 | RF23BB8600** | RF23BB8600** | 22.8 |
| RF23DB9600 | RF23D*9600** | RF23D*9600** | 22.8 |

## Findings about extraction

Model detection 6 and capacity detection 8 are on page 0 in all five saved OCR
records. The model glyph loss/substitution occurs despite model detection
confidence of 0.9941 and 0.97118. No threshold can be approved from these five
samples. The parser's `NO_WILDCARD_OBSERVED` means only that its extracted token
contains no star/question mark; it is not evidence that the original label has no
wildcards. Its full raw context must remain available, including the quotation
mark excluded from the model-like token.

All five raw capacity descriptors agree with the visible numeric value/unit.
Each full candidate file also contains a boilerplate line mentioning capacity
(`Both cost ranges based on models of similar size capacity.`). Candidate-list
length alone therefore cannot establish capacity ambiguity or select a value.
A future capacity selector must require a complete explicit Capacity descriptor
with numeric value/unit and its reviewed detection, rather than parse boilerplate.

## Implementation boundary

The next bounded implementation can be fixture-only capacity selection under the
already adopted conservative field-selection contract: explicit descriptor,
unambiguous numeric Cubic Feet value, reviewed document/page/panel/detection/box,
and matching raw candidate context. Preserve amount, source unit and full raw
descriptor. Missing units, conflicting descriptors, multiple panels/documents,
changed provenance or review mismatch must withhold a value. Capacity selection
must not depend on annual-energy selection: the RF22A4111 energy ambiguity does
not erase its independently observed capacity descriptor.

Live capacity remains disabled until fixture verification and saved-corpus replay.
Capacity is a source observation, not a PDP/EPA match criterion. No rounding,
numerical tolerance, discrepancy finding or independent identity corroboration
is enabled (D01/D07).

Model normalization, OCR character replacement and wildcard-to-SKU matching remain
disabled (D07/D09). Do not treat a star as arbitrary-length glob text, remove /AA
or AA, restore missing stars from filenames, or accept a prefix as an identity
match. Visible agreement for the other three groups also does not establish what
their wildcard positions mean. Keep original descriptors and review annotations
separate until an explicit correction/matching policy is approved.

## Verification

Offline regression cases replay the sanitized model/capacity descriptors through
the existing raw candidate parser. They require retention of the uncorrected raw
token and context, preservation of both descriptor and capacity boilerplate, and
disabled identity/correction states. They run in the cheap G2 contract workflow
on hosted Python 3.11/3.12; this review does not accept G2 or introduce a rule.

Local source-projection verification checked all nine SKU records against their
saved original PDF bytes and exact model/capacity detection text, page and polygon
coordinates. All matched. The local cheap contract suite passed 25 cases.
