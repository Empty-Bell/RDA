# Current Model Index exact-target candidate projection

This is a collection-definition contract. It produces no certification result,
publication finding or compliance assessment.

## Preconditions

The projector accepts only a replay-verified Current Model Index Samsung scan
with `COMPLETE_OBSERVED_QUERY`. Every target must carry an exact SKU, a
`VERIFIED_EXACT_IDENTITY` PDP gate, and the same execution ID as the scan.
This prevents a later product list from being joined to an unrelated EPA
snapshot.

## Candidate handling

For every target, retain every literal raw-SKU candidate and every literal
candidate produced by the approved terminal `AA` or `/AA` observation. Each
candidate retains its EPA page response hash, row ID, PD_ID, brand, raw model
number and CB identifier. The projector never chooses a first, latest or most
similar row.

`MATCHED_RAW_LITERAL_CANDIDATES` or
`MATCHED_APPROVED_NORMALIZED_LITERAL_CANDIDATES` means only that candidate
evidence was observed in the complete snapshot. The certification state and
assessment remain `NOT_EVALUATED` here.

If there is no literal candidate but the complete scan contains an EPA `*` or
`#` model encoding, the result is `UNRESOLVED_PATTERN_ENCODINGS_PRESENT` and
retains every such row reference. It cannot become an absence conclusion. Only
a complete scan without literal or pattern candidates can emit
`COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE`; this is still candidate-projection
output, not a certification or publication decision.

The reviewed refrigerator positional grammar is intentionally not applied by
this generic projector. It needs its strict p5st-her9 provenance and four-key
binding in the same execution before it can resolve a Current Model Index
pattern candidate.
