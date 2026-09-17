# Raw label-model source observations

The report may expose `label_model_raw` only as a source observation from the
EnergyGuide field-candidate record. It is not a normalized descriptor, an OCR
correction, an exact-SKU match, or an assessment input.

## Selection contract

The projection accepts exactly one nonempty `value_raw` candidate from a record
whose PDF SHA256 has the required lowercase 64-character format. It copies that
token byte-for-byte into the fact and report. Zero candidates, multiple
candidates, malformed candidates, or a missing value produce `NOT_OBSERVED`.

The source PDF, extractor result, and candidate record remain in the fact's
`evidence_ids`. Report replay rebuilds every displayed source-observation row
from the same-run bundle, so a displayed model token cannot be changed
independently of its source fact.

## Deliberate limits

The token may preserve OCR loss or substitution, including wildcard glyph loss.
No visible transcription replaces it. The system does not add or remove stars,
strip suffixes, expand patterns, compare it to PDP/EPA values, or infer product
identity. `label_model_normalized` remains `NOT_OBSERVED`.

This is a provenance projection only. It does not enable a rule, discrepancy,
finding, certification match, or legal conclusion.

## Hosted checkpoint

At commit `8d86408`, G1 fixture CI 35184128574 and G2 contract CI 35184128573
passed on GitHub-hosted runners. The live refrigerator observational run
35184128593 also passed on ubuntu-24.04 and preserved artifact 10481173998 with
ZIP digest `096e7a6a99d0c7c629410dd5506f2fc282e338c309db6fe0c454ebf4650dd8a9`.
That run collected the live source package and replay-verified its report rows;
it does not confer identity or assessment status on raw model strings.
