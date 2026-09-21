# Current Model Index and Samsung claim comparison

## Direction and activation boundary

The user selected EPA Current Model Index `8wj2-sec8` as the sole current
certification source. A verified model present in that list supplies current
certification evidence. The user explicitly approved the three-point publication
consistency rule: PLP logo, PDP logo and affirmative ENERGY STAR certification
in the exact-SKU Bridge Specs. The source-only collection boundary was also
approved; PLP `energyStarFlg`, PDP Next `energyStarFlag` and the exact-SKU
Bridge certification row supply those three points. The rule is implemented
below. Existing issue codes are reused; no new code is added.

This table is the executed Energy Star publication consistency rule:

| Current-index model result | PLP logo / PDP logo / Spec certification | Approved result |
|---|---|---|
| Registered | All three PRESENT | PASS for this EPA publication check |
| Registered | At least one confirmed ABSENT, including all three absent | LOW consistency finding: SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT |
| Registered | No confirmed absence, but at least one UNKNOWN | NOT_EVALUATED; never PASS |
| Not registered after validated complete search | At least one PRESENT | HIGH critical finding: CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE |
| Not registered after validated complete search | All three confirmed ABSENT | No ENERGY STAR publication finding |
| Not registered after validated complete search | No PRESENT, but at least one UNKNOWN | NOT_EVALUATED |
| Unresolved model or failed/incomplete current-index query | Any | NOT_EVALUATED for these certification-dependent rules |

The registered-model LOW rule is the user's publication consistency control;
it is not described as a legal requirement to advertise certification. One
missing point is sufficient even when the other two are absent. The HIGH rule
needs only one proven positive publication on an unregistered model. A proven
LOW/HIGH finding is retained even if another surface is UNKNOWN; incomplete
collection coverage remains visible separately and cannot yield overall PASS.
Store all missing/present point evidence in the applicable finding and avoid
creating three copies of the same rule finding. Other FTC or measurement checks
are independent; this table cannot produce whole-product compliance PASS.

## Inputs needed before assessment

### Samsung target and three publication points

Require the exact SKU population entry and existing PDP identity gate. Preserve
the full SKU and the approved uppercase terminal `AA`/`/AA` normalization;
preserve all preceding characters. The source page must identify that SKU.

Collect three independent surface observations: `plp_logo`, `pdp_logo` and
`spec_certification`. Each is PRESENT, confirmed ABSENT or UNKNOWN, with raw
text/image candidates, URL, capture time, evidence hash and SKU attribution.
PLP requires the correct listing card and explicit listing-group/SKU provenance;
a representative card must not silently supply every unrelated variant's state.
PDP requires the verified primary product surface. Spec requires affirmative
ENERGY STAR certification text/value in the visible target Spec table. A field
label with a negative, empty or unresolved value is not affirmative certification.
Keep its raw label/value and extraction reason. Exact supported label/value
aliases must be source-reviewed before normalization.

Footer, generic banners, recommendations, related products, ambiguous gallery
roots and unbound images cannot become target claims. A positive Spec value
cannot fill in a missing PLP or PDP logo. A PLP logo cannot fill in the Spec point.
The LOW rule counts an absent source declaration only after the exact-SKU source
capture is complete; missing capture, unsupported values or incomplete layout is
UNKNOWN.

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
strings. Literal equality and the approved fixed-position model patterns are
direct evidence from the same Current Model Index snapshot. No secondary EPA
dataset is queried. Unsupported model syntax remains UNKNOWN.

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

## Refrigerator Energy Star milestone status

1. **Complete.** Hosted complete Current Model Index Samsung-scope capture/replay, with actual
   category/type metadata and tested pagination/failure boundaries.
2. **Complete.** Exact-target candidate projection; preserve all row references and distinguish
   matched, complete no-match and unresolved comparisons without assessments.
3. **Complete.** Same-run, exact-SKU PLP PF flag, PDP Next flag and Bridge Spec
   certification rows were captured for all 75 refrigerator SKUs. Source
   evidence hashes are attached to the point records.
4. **Complete.** The sources were joined by same-run execution and exact SKU;
   the EPA pages replay from preserved hashes.
5. **Complete.** The approved rule runs after coverage checks and emits the
   existing LOW/HIGH issue codes. It reports only this Energy Star check;
   it does not decide whole-product compliance. Measurement and OCR policies
   remain separate G2 work.

Hosted assessment completed in run 35547213219 (artifact ZIP SHA-256
`93084dfa227992b883d86faee4fcd15f943051f9c6dfc36090011dcdb31c8072`): 75/75
exact SKUs evaluated, 43 PASS, 3 LOW, 24 HIGH, 5 NO_FINDING, and zero
NOT_EVALUATED or missing evidence references. This is the refrigerator Energy
Star publication check, not overall refrigerator compliance. For remaining
source plumbing or deterministic integration, use Terra medium; use Luna low
for documentation-only/offline maintenance. Reserve Sol medium for a genuinely
ambiguous rule or source interpretation.
