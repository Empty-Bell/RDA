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

Remaining work: review rendered originals for the other label hashes, bind review
annotations to PDF/page/region, then replay every saved candidate against the
selector on hosted Ubuntu. Capacity, wildcard identity, OCR corrections and
regulatory comparisons remain open. This review does not close G2.
