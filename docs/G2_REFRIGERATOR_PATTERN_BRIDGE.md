# Refrigerator pattern bridge

This step is an internal safety check. It does not expose EPA identifiers in a
product finding and it does not issue PASS, LOW or HIGH.

First, a GitHub Actions execution keeps only refrigerator SKUs whose Samsung
PDP was verified as the exact SKU. That is the target feed. It records the
same execution ID and PDP source hash for each target.

For a target such as `RF23DB9600QLAA`, the approved terminal suffix observation
supplies `RF23DB9600QL`. Before testing it against `RF23D*9600**`, the pipeline
asks EPA for the refrigerator row identified by the Current Model Index row's
PD_ID. The two EPA rows must match exactly on four internal fields: PD_ID,
brand, model pattern and CB identifier. This proves the pattern is the reviewed
refrigerator-source pattern, rather than an unrelated similarly written row.

Only then does the already-approved positional diagnostic run. A compatible
result becomes `PROVENANCE_BOUND_POSITIONAL_CANDIDATE`; it still means only that
EPA candidate evidence was observed. Any different execution ID, missing row,
duplicate row or four-field mismatch stops the bridge without a result.
