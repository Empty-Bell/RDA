# Refrigerator EPA candidate-linkage matrix proposal

Status: offline positional diagnostic v1 approved and implemented; no matching
semantics or certification identity is enabled. Scope is
`p5st-her9`, not Samsung EnergyGuide pattern interpretation.

## Reviewed evidence

The ZIP of original capture 35189522017 reproduced its published SHA256.
Its Product Finder HTML was a JavaScript shell, not the product record values.
That checkpoint proves raw capture/replay only. New hosted run 35189830486 at
`ef0da55` passed source-content tests and captures six sources, including the
literal PD_ID API query. Artifact 10483857141 reproduced ZIP digest
`8a799f87f8f9e0d1698e37c559f810ba4b810bc93f2eb1f37473601131cb1fd2`.

Preserved metadata describes `*` as a letter and `#` as a digit. Metadata SHA256
in the initial reviewed artifact is
`6fca2122b9db18d3ca53121b397606157c3de70d0237c1bee546a4ba10148b11`.
Together with QPX fixed-position guidance, this supports a possible dataset-scoped
candidate grammar, but does not approve it. Search-indexed export descriptions
suggesting alphanumeric stars are not equivalent to reviewed metadata. Retain the
disagreement; an adopted grammar must explicitly identify its governing source.

The new API body SHA256 is
`dfcc3c3c8a27447b114e75a8b43ec39318ad11fa36311707d4a760cb3872e3f3`.
PD_ID 2839420 returns Samsung `RF23D*9600**`, raw UPC string
`887276826820;887276826837;887276826844;887276826905`, markets
`United States, Canada`, raw annual energy `634`, and volume `22.8`.
`additional_model_information` is omitted (projected as null). That omission is
not proof that no additional models are represented by the certification.

The sanitized API projection is versioned at
`tests/fixtures/g2-epa-wildcard/api-record.json`. Hosted run 35190205775 at
`b283074` passed the six source-capture tests, including projection tampering,
ambiguous PD_ID response, malformed metadata and Product Finder shell handling.
Artifact 10483347557 has ZIP digest
`2fd920e4c8419fa1a90d7abfb0bb98bfb576b5410bac3a44aa72cac55d748aca`.

## Proposed matrix for later approval

| Condition | Candidate-linkage proposal | Remaining gates |
|---|---|---|
| Exact full Samsung model equals EPA model | Literal equality diagnostic under the existing approved contract | Brand, US market, current-version/certification and query completeness |
| Same-length literal retail model against EPA `*`/`#` pattern | Future positional diagnostic only: one ASCII letter per `*`, one ASCII digit per `#`; preserve raw strings | Governing grammar approval; literal-position agreement; no retail wildcards; no correction |
| Approved terminal Samsung `AA` or `/AA` suffix | Preserve full SKU and remove only the terminal suffix for an observational normalized identifier | Approved source-backed suffix contract; no removal of preceding configuration characters |
| Other extra suffix, space, case difference or different length | Withhold linkage; no folding or wildcard expansion | Explicit manufacturer identifier mapping |
| Damaged label token or uncertain wildcard count | Withhold label identity independently of EPA candidate diagnostics | Reviewed label evidence and approved D07 corroboration |
| Exact verified Samsung UPC found in EPA UPC field | Future association diagnostic, keeping every PD_ID and UPC as strings | Approved separator grammar, exact PDP attribution, no contradictory identifiers |
| Brackets, pipes, question marks or unsupported syntax | Withhold pattern interpretation | Separate source-scoped grammar contract |
| Multiple candidate records/specification versions | Preserve all; no first-row/latest-date winner | Approved current-certification precedence |
| Query/parser/access error | Fail source check; unknown linkage | Valid complete-query evidence; never absence/PASS |

For example `RF23DB9600QLAA` has two more positions than `RF23D*9600**`.
The full SKU remains preserved and does not fit directly. Under the approved
terminal `AA`/`/AA` observation, normalized `RF23DB9600QL` fits this pattern.
This records pattern inclusion only; energy/capacity agreement does not supply
other mappings, and no preceding configuration characters are removed.

The public dataset has no explicit certification-status column in the reviewed
column inventory. A date_qualified value, US market membership, or availability
alone must not imply current certification. Separate schema/source availability
from a later current-certification decision.

## Next authorized evidence work

Create small fixtures from the reviewed metadata and API record, preserving
source hashes and omitted-versus-present fields. Add projection replay tampering
and missing/ambiguous PD_ID cases to cheap hosted contracts. This requires no
matcher, wildcard normalization or new assessment state. Recommended model:
Luna low. Return to Sol medium only for approval of substantive linkage grammar.

## Concrete approval request: offline positional diagnostic v1

Approved only a fixture-tested diagnostic for preserved `p5st-her9` EPA patterns
against literal product identifiers. This is a new interpretation rule, beyond
the previously approved literal-equality diagnostic. It is not label matching,
current-certification selection, or a live pilot integration authorization.

The proposed contract requires:
- Dataset ID and reviewed metadata hash identifying the governing grammar.
  Missing evidence fails input validation; a changed source requires re-review.
- EPA pattern contains only uppercase ASCII letters, digits, `*`, and `#`.
  Target contains only uppercase ASCII letters and digits. Lowercase, spaces,
  slashes, question marks, brackets, pipes and target wildcards are unsupported;
  preserve the input and withhold interpretation. Uppercase-only is a proposed
  conservative project restriction, not a claimed universal EPA requirement.
- Equal full lengths. Every `*` consumes exactly one A–Z letter, every `#`
  exactly one 0–9 digit. All other positions require literal equality.
- No suffix removal, whitespace trimming, case folding, OCR substitutions,
  capacity/energy corroboration, UPC association or inferred wildcard restoration.
- Result describes only positional compatibility or its withheld reason.
  `identity_state` remains `NOT_EVALUATED`; correction remains `NOT_APPLIED`.
  No assessment, issue code, certification PASS or absence conclusion is emitted.

| EPA pattern | Literal target | Proposed result |
|---|---|---|
| `RF23D*9600**` | `RF23DB9600QL` | Positional compatible diagnostic only; hypothetical shortened token, not an approved identifier for a retail SKU |
| `RF23D*9600**` | `RF23DB9600QLAA` | Withheld: unequal length; retain complete retail SKU |
| `RF23D*9600**` | `RF23D89600QL` | Positional incompatible diagnostic only; digit cannot fill a letter slot |
| `ABC##` | `ABC01` | Positional compatible diagnostic only; synthetic digit-slot example |
| `ABC##` | `ABC/01` | Withheld: unsupported syntax |

After approval, implement only an offline helper and compact hosted fixtures on
Python 3.11/3.12, using Luna low. Load the versioned actual API projection in
tests; the preceding six-test checkpoint tested the parser with synthetic cases,
not that fixture's provenance. Add explicit raw-input immutability and source
binding cases. Neither the hosted fixture job nor the helper may fetch live data.
Live use, certification selection and suffix mappings require later review.

Implementation checkpoint: hosted run 35191030514 at `6c43029` passed the seven
source-capture/diagnostic tests on ubuntu-24.04. Artifact 10483914100 has ZIP
digest `23f308a90d76685e5206539a7f2fe65f568645394dbacb1464fc57c3125f259d`.

Corpus read-only checkpoint: run 35195946960 at `20ae644` applied the diagnostic
to nine saved refrigerator SKU observations. The artifact is 10486160033 with
ZIP digest `8b766e3c94b2e7bc557be6323fdfe52b877a0e6fc55ac7aa387d0c256ebfa20c`.
The report retained all raw SKU/model strings; slash-containing full SKUs were
withheld as unsupported syntax. No record received identity or correction state.
