# EPA query, type and update source contract

Status: query discovery PASS in run 35165385059; catalog/fixture regression pending.
Phase 0 RUNNING; D09 remains OPEN.

An anonymous, standard-library-only ubuntu-24.04 job probes each of the nine
distinct existing datasets. Shared routes (Range/Cooktop; Computer/Chromebook/Tablet)
are recorded without treating a shared dataset as approved product applicability.
Bounded official-domain catalog searches retain configured dataset advertisement
and other returned version entries, omitting publisher/contact fields. Advertisement
does not prove sole current version or current certification. Search failure/missing
configured ID fails the extraction probe without claiming the dataset is absent.
The EPA job installs no browser/OCR/LLM dependencies; concurrency is bounded to 3.

Declared exploratory scope is upper(brand_name) = 'SAMSUNG'. This is a literal
brand-string query, not all corporate aliases or all Samsung retail SKUs. Preserve
raw type, market, model, UPC and date values. Do not interpret wildcard characters,
strip SKU suffixes, infer UPC absence as mismatch, or filter US market by substring.

Page size 100, order :id, selected system row ID, limit 5000 diagnostic rows.
Require matching before/after counts, matching metadata update/schema fingerprints,
unique source row IDs, observed short terminal page and complete count. Exact-full
pages require a following empty page. Never truncate silently. Offset paging does
not provide transaction isolation; matching metadata/counts is observed stability,
not an atomic snapshot guarantee. Retain duplicate product certification IDs/models.

The first observed brand row seeds a model_number equality query with single quotes
escaped by doubling. Stars/question marks stay literal characters, not LIKE patterns.
This probes API equality, not matching a PDP SKU to an EPA certification.
Zero brand rows yields no exact-model probe and no absence/applicability finding.

HTTP errors, HTML, malformed JSON, error objects, non-record arrays, missing count
or identity fields, overlapping pages, truncation or source changes fail extraction.
A controlled 1=0 query verifies a valid empty array; a controlled malformed SoQL
query verifies HTTP 400 rejection. That intentional negative probe is recorded
separately from all normal requests, which must succeed. Neither response establishes
retail-product candidate absence. Failures preserve FAIL and response evidence.

Metadata retains schema/public timestamps and response hash, omitting publisher,
contact and account identifiers. Product/error response bytes are preserved before
JSON interpretation. Metadata identity/name and existing per-dataset columns are
independently validated against a generic sample even if the Samsung query is empty.

Update metadata is not model certification currency. date_qualified/date_certified
is not an expiry or withdrawal field. Record potential status/date fields and actual
values without inventing freshness cutoffs or certification rules. EPA documents
daily data updates and specification-driven dataset replacement; current status,
US market semantics, wildcard/variant routing and cross-version completeness remain
separate approval questions.

Intermediate artifacts: metadata-before/after.json, count/page JSON, response bytes
and recon.json with request/status/hash/provenance. Hosted artifacts retain 14 days;
compact manifests cannot replace a replay snapshot. Hosted PASS means extraction
contract verified, never certification, absence or G0 acceptance.

Primary references checked 2026-09-17:
- [Socrata text comparison and quote escaping](https://dev.socrata.com/docs/datatypes/text.html)
- [Socrata explicit paging order](https://dev.socrata.com/docs/queries/order.html)
- [EPA data tools / daily updates](https://www.energystar.gov/products/productstr)
- [EPA API dataset replacement process](https://www.energystar.gov/products/spec/energy_star_api_user_essentials_pd)

Discovery code 1f664cec4c2fd20fe03f82916fdd1cbab637b683 passed all nine EPA
jobs with seven query-boundary tests each. Actual full-query fixtures retain nine
datasets and controlled 400 responses; the fixture manifest records hashes/expiry.
Observed declared brand rows: refrigerator 101, dishwasher 22, washer 66, TV 59,
cooking 23, dryer 104, fan 0, displays 146, computers 45. These are query snapshot
counts, not retail SKU counts or per-SKU certification matching coverage.

Computers include Notebook and Slate/Tablet with some market strings excluding
United States. UPC omission is observed in multiple datasets, including most display
rows. Cooking has distinct product types; dryer/washer special_type includes combo
and laundry-center rows. Do not replace explicit source types with listing family.
Fan 0 rows means only this declared brand query returned zero; hood applicability
and other aliases remain OPEN. Pattern/variant equality and cross-version routing
require approved semantics. Current source advertisement is separately probed.

The local editing Python failed TLS trust verification for api.us.socrata.com;
no certificate-verification bypass was used. Catalog acceptance requires actual
hosted evidence, where OS trust roots and network are the target environment.
