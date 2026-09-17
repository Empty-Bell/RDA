# Refrigerator positional diagnostic corpus review

Hosted run 35195946960 applied the approved offline diagnostic to the nine
saved exact-SKU observations. This reviews diagnostic behavior only. The report
used `RF23D*9600**` as one candidate against each saved SKU to exercise
withholding; it did not claim this candidate belongs to every SKU.

| Diagnostic | Count | Interpretation |
|---|---:|---|
| `WITHHELD_UNSUPPORTED_SYNTAX` | 5 | Exact SKU contains `/AA`; suffix semantics were not invented |
| `WITHHELD_LENGTH_MISMATCH` | 4 | Exact SKU has more positions than the EPA pattern |
| Positional compatible | 0 | No identity or certification conclusion |

The visually matching family is `RF23D*9600**` for label group
`RF23DB9600QLAA`; its full SKU is longer, so the diagnostic correctly withheld
it. The four `RF23BB8600...` SKUs also remain length-mismatch observations.
Every output retains `identity_state=NOT_EVALUATED` and
`correction_state=NOT_APPLIED`.

The result does not justify stripping `/AA`, dropping regional suffixes,
restoring OCR stars, or treating the same pattern as a family match for all
records. Without a source-backed Samsung suffix contract, positional diagnostics
cannot be applied to common Samsung exact SKU strings. That limitation is safer
than inventing identity.

Keep v1 unchanged. Add a future suffix observation only after Samsung
documentation or an explicit manufacturer/EPA additional-model record states
what `/AA`, `AA`, and preceding configuration characters mean. Preserve the
full SKU, source URL/hash, and whether the split is source-declared or a parser
proposal. It must not feed identity matching until a separate D09 approval.

The reviewed PD_ID record has null `additional_model_information`, so it supplies
no additional-model mapping. Capacity or annual-energy agreement cannot replace
that missing mapping. No collector, fact, match, assessment, issue code or
dashboard output changed.
