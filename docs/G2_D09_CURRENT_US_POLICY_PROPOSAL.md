# Refrigerator EPA current-status and US-applicability proposal

Status: user approved the bounded US-market observation on continuation after
the market explanation. Current-status assessment remains disabled.
It follows the approved Samsung terminal `AA`/`/AA`
normalization and EPA positional-pattern inclusion observation. It does not
activate an assessment, issue code, certification PASS, or absence finding.

The preserved `p5st-her9` row for PD_ID `2839420` has Samsung
`RF23D*9600**`, `markets=United States, Canada`, and
`date_qualified=2023-12-11`. The reviewed schema has no explicit current or
withdrawn-status column. Its pattern includes normalized `RF23DB9600QL`, which
comes from source-observed SKU `RF23DB9600QLAA` under the approved suffix rule.

| Output | Proposed value for saved row | Meaning |
|---|---|---|
| `model_pattern_inclusion` | `INCLUDED` | Fits this preserved EPA pattern |
| `current_certification_state` | `NOT_EVALUATED` | No source states current/withdrawn status |
| `us_applicability_state` | `OBSERVED_US_MARKET` | Literal `United States` token observed in the EPA row |
| `assessment` | `NOT_EVALUATED` | No compliance conclusion follows |

## Approved observation boundary

1. A successfully captured, schema-validated EPA row whose `markets` lists
   literal `United States` may set `us_applicability_state=OBSERVED_US_MARKET`.
   This is a source-market observation, not a regulatory applicability finding.
2. No field in the reviewed refrigerator schema can set
   `current_certification_state=CURRENT`. It remains `NOT_EVALUATED` until an
   explicit current/withdrawn source and a refresh-precedence rule are reviewed.
3. Pattern inclusion, observed US market and current status remain independent.
   The first two do not imply the third or an assessment result.
4. Multiple matching rows are preserved. A newer `date_qualified` does not win
   automatically; an incomplete query cannot imply no candidate.

The report must preserve raw markets/date, PD_ID, source URL and response hash.
Missing markets means `NOT_EVALUATED`, not non-US. A source failure cannot
produce a negative conclusion. Implementation is limited to the offline
projector with literal US, non-US, missing/malformed markets and source-failure
tests; no candidate precedence or deduplication is activated. The report implements exact comma-delimited token
observation and records `EPA_ROW_ONLY` scope, including on nonmatching corpus
SKUs. Thus the state does not imply a SKU-to-row association. Recommended model:
Terra medium; fixture-only changes: Luna low.
