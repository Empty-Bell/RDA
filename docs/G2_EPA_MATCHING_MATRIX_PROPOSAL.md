# Refrigerator EPA candidate-linkage matrix proposal

Status: review draft, no matching semantics approved or enabled. Scope is
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
| Extra suffix, slash, space, case difference or different length | Withhold linkage; no stripping, folding or wildcard expansion | Explicit manufacturer identifier mapping |
| Damaged label token or uncertain wildcard count | Withhold label identity independently of EPA candidate diagnostics | Reviewed label evidence and approved D07 corroboration |
| Exact verified Samsung UPC found in EPA UPC field | Future association diagnostic, keeping every PD_ID and UPC as strings | Approved separator grammar, exact PDP attribution, no contradictory identifiers |
| Brackets, pipes, question marks or unsupported syntax | Withhold pattern interpretation | Separate source-scoped grammar contract |
| Multiple candidate records/specification versions | Preserve all; no first-row/latest-date winner | Approved current-certification precedence |
| Query/parser/access error | Fail source check; unknown linkage | Valid complete-query evidence; never absence/PASS |

For example `RF23DB9600QLAA` has two more positions than `RF23D*9600**`.
The proposed strict grammar would withhold that full-SKU linkage. Removing `AA`
to obtain a fit requires a separate approved mapping; energy/capacity agreement
cannot supply it. Similar reasoning applies to slash-containing SKUs.

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
