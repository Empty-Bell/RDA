# EPA current certification source reconnaissance

Research date: 2026-09-17. Documentation and read-only API reconnaissance only;
no runtime certification rule or G2 acceptance is activated by this record.

## Official source meaning

[EPA Model Index catalog](https://catalog.data.gov/dataset/energy-star-model-index)
and [EPA metadata](https://data.energystar.gov/api/views/8wj2-sec8.json) describe
dataset `8wj2-sec8` as a list of currently certified models across product
categories. It has `pd_id`, brand, product category/type, model number, markets,
date certified and CB model identifier. It can provide a current-list snapshot
observation that the category dataset's certification date alone cannot provide.

The read-only query `pd_id=2839420`, limit 2, returned one Model Index row:
Samsung, `RF23D*9600**`, Consumer Refrigeration Products,
Refrigerators or Refrigerator-Freezers, United States/Canada and CB identifier
`ES_1023593_RF23D*9600**_12112023144226_80192002`. The PD_ID, brand, model and
CB identifier agree with the saved refrigerator row. This is promising evidence,
but this research query is not a hosted raw/hash capture or an implemented join.

## Next capture and validation contract

On standard hosted Ubuntu, preserve Model Index metadata and literal PD_ID
query bytes before parsing. Record capture time, metadata row-update time,
response hash, requested/final URL and HTTP status. Validate dataset ID and
required fields; require exactly one queried PD_ID row and exact brand/model/CB
identifier agreement with the separately preserved category row. A mismatch,
duplicate, empty response or source failure must withhold a positive observation.

Use sanitized actual fixtures and offline 3.11/3.12 tests for matching keys,
changed model/brand/CB identifier, missing row, duplicates and failed capture.
Separate manual live capture from cheap fixture CI.

After capture validation, propose a time-scoped
`OBSERVED_CURRENT_CERTIFIED_INDEX` state with the snapshot's source timestamps.
It must never mean perpetual certification or absence of later withdrawal.
Absence from the index alone cannot produce certification PASS; stale, missing or
conflicting snapshots cannot either. Preserve every candidate rather than
selecting the latest date automatically. This research completes the
source-discovery subtask, not the G2 gate.
Next model: Terra medium for bounded hosted capture/fixture integration; Sol
medium only for adopting the snapshot-state and conflict/refresh policy.

## Hosted evidence and approval proposal

Hosted run [35208691273](https://github.com/Empty-Bell/RDA/actions/runs/35208691273)
captured the three source responses on `ubuntu-24.04`; its artifact ZIP digest is
`8b7f7022ef172f67210990989c171b76d38b550e5a6878729524d6a43cc7e111`.
The Model Index metadata, Model Index PD_ID row and refrigerator PD_ID row were
all HTTP 200. Their Model Index row/refrigerator row values agreed on PD_ID,
brand, model pattern and CB identifier. The latter raw body SHA-256 is the
previously preserved `dfcc3c3c8a27447b114e75a8b43ec39318ad11fa36311707d4a760cb3872e3f3`.
Hosted run [35210140588](https://github.com/Empty-Bell/RDA/actions/runs/35210140588)
passed the replay-tamper contract on Python 3.11 and 3.12.

Proposed approval: when a same-run, schema-validated Model Index row and
category row have one exact match on all four keys, emit
`current_certification_state=OBSERVED_CURRENT_CERTIFIED_INDEX`. Include the
capture timestamp, Model Index metadata update timestamp, both raw source hashes
and the four key values. This means the row appeared in EPA's current-certified
Model Index at that capture snapshot only. A missing, duplicate, mismatched,
failed, stale or conflicting source produces `NOT_EVALUATED`.

## Approved implementation

The approved rule is implemented in the offline diagnostic report v4. The
saved Model Index projection from the hosted capture is treated as a snapshot
source. Only exact equality of `pd_id`, `brand_name`, `model_number` and
`energy_star_model_identifier` with the saved refrigerator projection emits
`OBSERVED_CURRENT_CERTIFIED_INDEX`. The report preserves the Model Index raw
body hash and `date_certified` alongside that observation.

This implementation records a point-in-time source observation only. It does
not emit a compliance finding, certification PASS or an inference from absence.
Missing or disagreeing keys emit `NOT_EVALUATED`. The Current Model Index is the
sole EPA certification comparison source. Recommended model: Terra medium.
