# Current Model Index and Samsung claim comparison

## Direction and activation boundary

The user selected EPA Current Model Index `8wj2-sec8` as the sole current
certification source. A verified model present in that list supplies current
certification evidence. A verified model absent from a successfully completed
current-list scan, but advertised with an ENERGY STAR claim, is the intended
claim-consistency failure case. Assessment remains disabled until collection
definitions and their verification are complete. No new issue code is added.

This table documents the intended behavior for later implementation, not a
currently executing compliance rule:

| Verified target claim | Complete current-index comparison | Intended EPA claim-consistency result |
|---|---|---|
| Positive logo or visible certification assertion | Matching current US-market model observed | PASS for this claim check only |
| Positive logo or visible certification assertion | No matching model in the validated complete scope | FAIL for this claim check only |
| No positive claim observed on supported inspected surfaces | Matching model or no matching model | No unsupported-certification-claim finding |
| Unknown target claim, failed identity or failed/incomplete current-index query | Any | NOT_EVALUATED |
| Positive claim | Ambiguous model syntax, conflicting candidates or unresolved market | NOT_EVALUATED |

Certification does not require Samsung to display a logo. Therefore a certified
model without a logo is not a failure under this check. Other FTC or measurement
checks are independent; this table cannot produce whole-product compliance PASS.

## Inputs needed before assessment

### Samsung target and claim

Require the exact SKU population entry and existing PDP identity gate. Preserve
the full SKU and the approved uppercase terminal `AA`/`/AA` normalization;
preserve all preceding characters. The source page must identify that SKU.

Use a visible ENERGY STAR logo attributed to the verified primary product
surface, or an explicit visible certification assertion in that SKU's supported
Specs/product surface. Preserve the raw text or image candidate, URL, timestamp,
evidence hash and target identity. Footer, recommendations, related products,
ambiguous gallery roots and unbound images cannot become target claims.

Structured flags remain separate source signals. A raw `energyStarFlag=Y` alone
does not establish a visible logo or advertised assertion. `N` or an absent flag
does not cancel a visible positive claim. Unsupported or unread surfaces are
unknown, rather than confirmed absence of a claim.

### EPA complete current-list snapshot

Capture Current Model Index metadata and all pages for the declared Samsung
brand scope. Validate the actual metadata field names and explicit product
category/type values before introducing a refrigerator-only filter. Never guess
field names or silently exclude unknown type values.

Reuse the existing bounded EPA query contract: count before/after, deterministic
ordering, preserved pages, terminal-page evidence, complete row-count agreement,
duplicate identity controls and unchanged update metadata. Preserve the literal
query, capture interval, row update time, raw URLs/hashes and scan scope.
Unchanged metadata is a stability check, not proof of a transactionally atomic
API snapshot. Any detected change or unresolved completeness issue withholds a
negative result. Sources must be freshly collected in the audit run; saved review
fixtures cannot supply a live current-certification verdict.

An empty single-PD_ID query or mismatch to one saved EPA row cannot establish
that a SKU is absent from the current list. An exhausted complete scope can do
so only after all its candidate comparisons are resolved.

### Model comparison and market

Compare verified raw/normalized Samsung targets to Current Model Index model
strings. Literal equality is direct evidence. For the reviewed refrigerator
pattern, retain the approved single-position grammar and the exact four-key
binding to p5st-her9 provenance; the category dataset supplies grammar provenance
only, not an alternate current-certification verdict. Do not apply that grammar
to unrelated datasets, labels or unsupported pattern syntax.

Keep all candidates. Do not choose a row by latest date, similarity, prefix or
numerical energy/capacity equality. Unknown pattern encodings prevent an absence
verdict until their candidate relevance is resolved. A positive current US
observation also retains the row's literal `United States` market token. Missing
or unresolved market is withheld; it is not an automatic non-certified result.

## Actual saved example and current limitations

Samsung source SKU `RF23DB9600QLAA` normalizes to `RF23DB9600QL`. The preserved
EPA pattern `RF23D*9600**` includes that target. PD_ID `2839420`, brand, pattern
and CB identifier agree between the saved refrigerator row and current-index
row captured in hosted run 35208691273. This is a source-backed example of
current model-pattern evidence, not a completed live claim-consistency assessment.
No same-run positive visible claim is established by this document.

Saved SKU `RF18A5101SR/AA` does not fit that one pattern. Its current status
remains unresolved until the whole declared index scope is searched. The
diagnostic report's current-index observation concerns the compared EPA row,
not every SKU printed beside it; `current_index_observation_scope=EPA_ROW_ONLY`
makes that boundary explicit.

## Remaining collection-definition milestones

1. Hosted complete Current Model Index Samsung-scope capture/replay, with actual
   category/type metadata and tested pagination/failure boundaries.
2. Exact-target candidate projection; preserve all row references and distinguish
   matched, complete no-match and unresolved comparisons without assessments.
3. Same-run target-attributed logo/visible-claim projection with failure and
   unsupported-surface states; establish full refrigerator collection coverage.
4. Join the observations by run/SKU/evidence identity and validate replay.
5. Review collection completeness, then activate the intended decision table
   with boundary tests. Other unresolved measurement/OCR policies remain separate.

Next recommended model: Terra medium for milestone 1 and its bounded contracts.
Use Luna low for documentation-only maintenance and Sol medium only when an
unresolved comparison or assessment meaning requires a decision.
