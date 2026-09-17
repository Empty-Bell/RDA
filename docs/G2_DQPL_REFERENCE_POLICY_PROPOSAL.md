# Refrigerator DQPL model-reference policy proposal

Status: DRAFT; implementation and semantic approval pending. This policy is
limited to a source-reference observation, not a compliance rule or final
certification decision. Existing Samsung suffix approval remains effective;
the proposed use of its output for DQPL comparison is reviewed here explicitly.

## Evidence and meaning

Hosted raw capture 35216830202 and reviewed XLSX hash
`adc06486f4ef3e0cd3aaf9d1e45fd9be808f568d4478203641dbee2ec17b6958`
bind the 2,997 rows to capture time `2026-09-17T11:39:29.251264+00:00`.
The source states `1/1/2018 to 5/15/2026`. Read-only inspection found zero
rows with Brand Name literally `Samsung`, and zero source-text candidates with
`samsung` in the case-insensitive brand/organization text. These observations
are confined to this snapshot; the latter search is reconnaissance only and
does not define brand aliases or product identity.

[EPA's Integrity page](https://www.energystar.gov/partner-resources/products_partner_resources/products_integrity)
links the list separately from certified-product sources.
[EPA procedures, February 2018](https://www.energystar.gov/sites/default/files/asset/document/Disqualification_Procedures_0.pdf)
describe certification withdrawal and posting after removal from the qualified
list. They also prohibit recertifying a new product with a previously
disqualified model number. Therefore simultaneous references in both sources
require evidence review; dates alone do not establish a valid recertification.
These documents do not provide a DQPL wildcard grammar or Samsung alias table.

## Proposed comparison boundary

| Check | Proposed positive-reference condition | Otherwise |
|---|---|---|
| Provenance | Successful raw capture; replayed body and saved row observations; valid sheet and headers | Withhold query result |
| Category | Literal `Refrigerators and Freezers` | Preserve other categories; no substring mapping |
| Brand | Literal `Samsung` in Brand Name | No organization-to-brand inference or aliasing |
| Target identity | Verified Samsung exact SKU and preserved raw SKU | Withhold target comparison |
| Model | DQPL text equals raw exact SKU, or equals the user's approved terminal-AA-normalized Samsung SKU | No prefix, glob, edit-distance or wildcard interpretation |
| Model encoding | Shared-string or inline-string cell; original value remains unchanged | Numeric/error/formula encodings require separate review |
| Date and scope | Valid source date within the stated source interval and no future event relative to capture | Preserve row as unresolved; withhold positive reference |

The Samsung-side transformation removes only terminal uppercase `AA` or `/AA`;
all preceding characters remain. The DQPL model text receives no suffix stripping,
case folding, trimming or OCR correction. Record both targets and which exact
comparison produced each reference. Do not inherit p5st-her9 wildcard grammar.
The raw stated interval is preserved and parsed independently of the capture
date; a later capture date does not extend the list's stated interval.

## Proposed outputs and conflict handling

For every qualifying exact source reference, emit
`dqpl_reference_state=OBSERVED_DQPL_MODEL_REFERENCE`, retaining workbook hash,
capture time, stated interval, sheet/row/cell references, raw fields, comparison
target and transformation provenance. This means only that this dated source
references that model text. Product identity, disqualification assessment and
compliance assessment remain `NOT_EVALUATED`.

If no qualifying reference is found in a successfully validated complete scan,
record `dqpl_reference_state=NOT_OBSERVED_IN_SOURCE_SNAPSHOT` with the query
scope and source interval. It must never mean NOT_DISQUALIFIED, CURRENTLY_VALID,
certification PASS or absence of lifetime disqualification. Failure or unresolved
candidate encodings yield `NOT_EVALUATED`, not an empty successful query.

Retain every candidate row, including duplicates; do not select a latest date.
If both a DQPL reference and an approved Current Model Index observation concern
the target, expose both evidence sets and a separate conflict-review diagnostic.
Neither source overwrites the other and no certification PASS is produced.
The historical DQPL reference does not expire solely because its event is old.

## Concrete examples

Observed Samsung SKU `RF23DB9600QLAA` normalizes to `RF23DB9600QL`; its EPA
pattern `RF23D*9600**` includes that target under the approved refrigerator
policy. The reviewed DQPL has no Samsung source-text candidates. The proposed
output for a fully validated scan would therefore be
`NOT_OBSERVED_IN_SOURCE_SNAPSHOT`, explicitly scoped to the 2018-01-01 through
2026-05-15 list, while keeping the independent current-index observation.
This is not a final assessment of RF23DB9600QLAA.

Actual DQPL row 6 has category `Roofing Products`, brand `PVDF`, numeric model
cell E6 value `106`, and date serial F6 `43770`. It remains source evidence; it
cannot become a Samsung refrigerator reference through type conversion or a
category substring search.

## Required verification before implementation acceptance

Hosted Python 3.11/3.12 fixtures must cover literal references, normalized
Samsung-side targets, untouched source text, category/brand mismatches,
wildcard withholding, numeric/formula/error encodings, missing and invalid dates,
out-of-interval dates, preserved duplicates, failed/incomplete scan, saved-output
tampering and current-index conflict. Counts and capture IDs remain source-derived.

Before live acceptance, close observation-parser integrity gaps found during
review: verify the saved `observations.json` bytes against the manifest as well
as recomputing output; reject duplicate XML row/cell coordinates rather than
silently overwriting them; preserve formula and number-format metadata; expand
sanitized fixtures for these paths. The previous hosted fixture PASS does not
establish these untested behaviors or a full live v2 acceptance.

## Approval requested

Approve the refrigerator-only literal source-reference conditions and bounded
observational states above, including Samsung-side terminal-AA normalization.
No issue code, compliance rule, PASS/FAIL assessment, DQPL wildcard matcher,
brand alias table or inference from absence is authorized by this approval.
AGENTS.md items 2 and 3 require semantic decisions to be explicit before
implementation; this draft is the concrete review object for that decision.

Next model: Terra medium for parser-integrity fixes and approved observation
implementation. Sol medium is needed only if the comparison/scope policy changes.
