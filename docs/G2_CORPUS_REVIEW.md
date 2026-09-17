# Expanded EnergyGuide corpus review

Structural review PASS; canonical activation remains pending visual review.
Source run 35176346751 / ddad8ff, artifact 10478339474. Downloaded ZIP SHA256
6c16c394b39837c30e4c5f7d1b0b6aab34ac051394aebc67062836072531a599
matches GitHub metadata. Download used the GitHub connector; no live crawl repeated.

Bundle validation and all 166 evidence file hashes passed. Twenty facts cover
ten PDPs and ten labels. Population 75: verified PDP 10, failed 0, unattempted 65.
EPA remains 101-row query context, not SKU certification matching.

Nine additional label observations each have one PDF page and one geometry
proposal. Raw annual text candidates: RF18A5101MT/S9/SR = 540;
RF22A4111SR = 109 and 585; RF22A4221SR = 585;
RF23BB860012/04M/0QL = 621; RF23DB9600QL = 634.
These are candidate observations, not accepted canonical values.

Rendered RF22A4111SR label review confirms $109 is a cost-range endpoint and
585 kWh is annual electricity use. OCR dropped the currency marker, allowing the
nearby-order parser to create an extra 109 kWh candidate. The conservative
selector must abstain; it must not silently discard or correct that candidate.
The projected actual records are retained in the rf22a4111 fixture.

Selector audit found that the earlier implementation did not enforce unique
geometry proposals or explicit document/panel review. The corrected selector
requires PDF-bound single-document/all-page/US-panel review, matching page, explicit
kWh and exactly one geometry proposal; default invocation abstains. No live
canonical fact has been enabled. Text/geometry remain correlated OCR evidence.

All five distinct additional-label OCR-input renders were visually reviewed.
Shared PDF hashes let one render review cover the corresponding source bytes,
but do not independently establish SKU applicability. Visible annual values are
540 (RF18A5101 group), 585 (both RF22 groups), 621 (RF23BB8600 group), and
634 (RF23DB9600). Model wildcards remain uncorrected. This is visual review of
the preserved 2x render, not an independent second OCR engine.

Strengthened fixture gate run 35179047280 at 234dfd2 passed on hosted Python
3.11/3.12 (18 contracts). No live canonical selector was enabled.

Review annotations in `docs/evidence/g2-label-review-annotations.json` bind each
rendered PDF hash to its page, caption, number, and unit detection IDs. They are
limited to the saved artifact and cannot enable a comparison. The selector checks
those IDs before yielding a value.

Offline replay recorded in `docs/evidence/g2-label-corpus-replay.json` PASSed all
nine reviewed SKU records: eight unique observations were retained and
RF22A4111SR/AA remained `NOT_OBSERVED`. The latter outcome preserves the $109 / 585
OCR ambiguity rather than treating visual review as an OCR correction.

Live review-bound integration checkpoint PASS: hosted run 35179885437 at 1cd83df
collected a fresh bounded refrigerator package on ubuntu-24.04. Each live label is
eligible for an `annual_energy_kwh` VALUE only when its exact SKU, PDF SHA256,
reviewed page and detection IDs all still agree; an unreviewed SKU or changed PDF
records `NOT_OBSERVED` while preserving raw source evidence. Artifact
10480785114 has ZIP digest
`bffd5d342f7a2f2f930f9a4f126562632b8fc99d217bd2832bd2e9c4eb9dc9a8`.
Assessments, comparison and EPA matching remain disabled.

Remaining work: replay every saved candidate against the selector on hosted
Ubuntu. Capacity, wildcard identity, OCR corrections and regulatory comparisons
remain open. This review does not close G2.
