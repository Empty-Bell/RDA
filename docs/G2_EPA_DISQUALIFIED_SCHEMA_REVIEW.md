# EPA disqualified XLSX schema review

## Reviewed evidence

Read-only review of artifact 10495336944 from hosted capture
[35216830202](https://github.com/Empty-Bell/RDA/actions/runs/35216830202).
The downloaded ZIP matched the recorded SHA-256
`78f40271db8dad87c6ebf11c8bf3f854245da47117a15f2ba9cefe3b38738ffd`.
The XLSX body hash is
`adc06486f4ef3e0cd3aaf9d1e45fd9be808f568d4478203641dbee2ec17b6958`.
Capture timestamp: `2026-09-17T11:39:29.251264+00:00`.
Bundled Python/openpyxl inspected the workbook metadata and first rows; a
one-off standard-library OOXML inspection counted value-bearing rows and raw
cell types. No production parser, model matching or assessment was added.
Compact observations: `docs/evidence/g2-disqualified-schema-review.json`.

## Source layout and scope

One sheet, `Disqualified Products List`. B2 contains the list title, B3 contains
the source's stated interval `1/1/2018 to 5/15/2026`, and B4 describes testing
failures against ENERGY STAR Program Requirements. These are source statements,
not evidence of complete coverage after May 15 or before January 2018.

The header is B5:F5:

| Column | Exact source header | Proposed raw observation |
|---|---|---|
| B | Product Type | Source category text and cell reference |
| C | Organization Name | Organization text, independent of brand |
| D | Brand Name | Brand text, no approved name aliasing |
| E | Product Model Number | Cell value/type/format, no identifier correction |
| F | Date Disqualified | Raw value/type/format and workbook date system |

Rows with values extend through row 3002. There are 2,997 value-bearing rows
after the header in this snapshot, with B:F populated in each. The worksheet
dimension is `A1:H1048027`; its large dimension must not be used as a product
count. No formula cells were observed. B2:F2, B3:F3 and B4:F4 are merged.

Of the observed model cells, 2,814 are shared-string cells and 183 are numeric.
For example E6 is numeric raw value `106`, while F6 is raw Excel date serial
`43770`; read-only openpyxl interprets the latter as 2019-11-01. An identifier
must not become a floating-point rendering such as `106.0`. A date serial is
not a model number, and neither should be converted without preserving its
original value/type/format. The workbook does not set `date1904`.

Raw category labels include both `LED Lamps` and `LED Lamps `, and both
`Luminaires` and `Luminaires `. Preserve these differences. The snapshot has
52 rows labeled `Refrigerators and Freezers` and 35 labeled
`Commercial Refrigerators and Freezers`; they must not be merged by a substring
test. These counts describe this reviewed source only.

No PD_ID, CB model identifier, US-market field or certification date is present
in B5:F5. The four-key Current Model Index join cannot be reused here.

## Proposed next source-observation contract

1. Bind every observation to the raw workbook hash, capture timestamp, stated
   interval, sheet name, row and exact cell references.
2. Verify the sheet and five exact header names before projecting source rows;
   schema changes withhold extraction and never become a product PASS.
3. Read value-bearing rows, ignoring format-only rows. Retain partial, duplicate
   and repeated records with explicit diagnostics; do not silently deduplicate
   or forward-fill cells.
4. Preserve cell value, OOXML type, style/number format and workbook date system.
   Keep organization, brand and model independent. Unknown encodings remain
   unresolved observations.
5. Record source-list observations only, with product identity, disqualification
   assessment and compliance assessment all `NOT_EVALUATED`.
6. Test sanitized cases for inflated worksheet dimensions, numeric identifiers,
   date encodings, trailing spaces, missing fields, duplicate rows, changed
   headers and failed/raw-hash-mismatched captures on hosted Python 3.11/3.12.

This contract can support a bounded observation parser without deciding model
identity. Before model comparison, review category scope, brand aliases,
model-string grammar, historical interval and conflicts with the current index.
The p5st-her9 wildcard and Samsung terminal-AA policies do not automatically
become DQPL matching rules. Absence from this dated list cannot establish that a
product has never been disqualified or is currently certified.

Review status: COMPLETE for this source snapshot. Production observation parser
and matching policy remain unimplemented. G2 acceptance remains pending.
Next recommended model: Terra medium for the bounded observation parser and
failure-path fixtures; reserve Sol medium for identifier/scope policy decisions.
