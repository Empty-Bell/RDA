# Samsung model suffix source review

Research date: 2026-09-17. G2 remains RUNNING. The user approved a bounded
Samsung terminal-suffix normalization: remove only terminal `AA` or `/AA` from
an uppercase exact SKU, preserving every preceding character and the raw input.
This approval does not establish EPA identity, certification, current status,
US applicability, or a compliance assessment.

## Source observations

| Official source | Observed text | Supported conclusion |
|---|---|---|
| [Samsung US RF23DB9600QLAA PDP](https://www.samsung.com/us/refrigerators/french-door/bespoke-counter-depth-4-door-flex-refrigerator-23-cu-ft-with-beverage-center-in-stainless-steel-sku-rf23db9600qlaa/) | `RF23DB9600QL / RF23DB9600QLAA` | Manufacturer displays these two identifiers together on this specific product page |
| [Samsung US refrigerator support](https://www.samsung.com/us/support/troubleshoot/TSG10003246/) | `RF18A5101**/RF20A5101**` in heading; `RF18A5101 / RF20A5101` below | Family-level notation exists, but this page does not bind the three saved exact RF18 SKUs to an EPA record |
| [Samsung RF18 specification PDF](https://image-us.samsung.com/SamsungUS/home/06072023/RF18A5101SR_V12.pdf) | `RF18A5101` heading | Family designation is insufficient to establish a general suffix grammar |
| [Samsung Caribbean RF18 PDP](https://www.samsung.com/latin_en/refrigerators/french-door/rf5000a-17-5-cu-ft-silver-rf18a5101sr-aa/) | `RF18A5101SR/AA` | `/AA` also appears outside the US site; do not infer US certification market solely from it |

The bounded search did not establish what every trailing `AA` or `/AA` means,
or a universal deletion rule. This is an unresolved evidence gap, not proof that
Samsung has no such documentation. Search snippets and web-rendered text are
research references, not raw pipeline artifacts with verified response hashes.

The RF23 paired display offers a concrete manufacturer-declared observation
without inventing a string transformation. The reviewed EPA PD_ID 2839420 has
`model_number=RF23D*9600**` and null `additional_model_information`; it does not
explicitly list either Samsung identifier. Applying the approved offline
diagnostic to the source-displayed short identifier could test positional
compatibility only. It cannot establish certification identity, current status,
US applicability, or the absence of conflicting candidates.

The approved rule maps `RF23DB9600QLAA` to `RF23DB9600QL` and
`RF18A5101SR/AA` to `RF18A5101SR`. It does not remove configuration characters
such as `QL` or `SR`, repair OCR, accept lower case or embedded suffixes, or
permit a broader family match. Its output remains an observational normalized
identifier with `identity_state=NOT_EVALUATED`.

## Next bounded implementation

1. Capture the RF23 official PDP on standard `ubuntu-24.04`, preserving response
   bytes, final URL, HTTP status and SHA-256 before extracting identifiers. Reuse
   the existing desktop user-agent and source failure boundaries.
2. Extract only a source-declared paired model field. Preserve full raw field,
   both literal tokens, source location and evidence hash. A slash alone is not
   a delimiter contract: other fields contain literal SKU `/AA`. Ambiguous,
   missing, duplicated or contradictory fields must be withheld or fail the
   collection contract; never derive a short token by dropping characters.
3. Bind a sanitized actual fixture to its source artifact and add offline tests
   for this field, literal `/AA`, ambiguous pairs, and changed/missing content.
   Run offline fixture checks on hosted Python 3.11/3.12 independently of live
   capture. Docs and fixture-only edits must not trigger live collection.
4. Keep outputs observational. Any diagnostic on the declared short token must
   retain the original full SKU and the paired-field provenance. No automatic
   EPA candidate attribution or assessment. D09 remains OPEN.

Checkpoint validation: verify hosted raw artifact hash and extracted field
against the actual source; check replay equality and negative fixture outcomes.
Do not report a G2 acceptance until its wider gate requirements are met.

Recommended next model: Terra medium for this bounded collector integration;
Luna low for subsequent fixture-only or documentation changes. Sol medium is
reserved for a substantive identity-policy decision. No runtime LLM is needed.

## Implemented capture boundary

`g2_samsung_pair_capture.py` implements the bounded capture described above.
It accepts exactly one literal `RF23DB9600QL / RF23DB9600QLAA` field from the
official PDP response and preserves the raw response before projecting it. A
missing or repeated field, failed response, hash change, or changed projection
fails. The parser does not apply to `/AA` SKU text, nor does it construct a
short identifier by deleting characters.

`g2-offline-source-contracts.yml` runs the sanitized fixture contracts on hosted
Ubuntu Python 3.11 and 3.12 for relevant code and fixture changes. The live
Samsung capture is manual-only in `g2-samsung-pair-capture.yml`, so a cheap
contract edit does not make an external request. Its artifact remains the
required evidence before this observation can be treated as source-captured.

## Hosted capture checkpoint

GitHub Actions run [35202527763](https://github.com/Empty-Bell/RDA/actions/runs/35202527763)
passed on `ubuntu-24.04` at commit `1767639`. The uploaded artifact
`g2-samsung-pair-35202527763-1` has SHA-256
`1b0746f1016f262dcc78f5e522fe1ba577140333620edef818390ae52d808296`.
Its downloaded ZIP matched that digest.

The preserved Samsung response was HTTP 200, `text/html; charset=utf-8`,
797,788 bytes, SHA-256
`f80ae3467d0247f356824a239d1d7b83d228fa872bb0747836014dca992e0b25`.
The raw declared field was `RF23DB9600QL /  RF23DB9600QLAA` (two spaces after
the slash); projection preserved this raw text and separately recorded literal
left `RF23DB9600QL` and right `RF23DB9600QLAA` tokens. Replay completed in the
hosted collector before artifact upload. This is manufacturer source evidence
for this one displayed pair only. It neither strips `AA`/`/AA` elsewhere nor
sets EPA identity, certification status, market applicability, or assessment.

## EPA additional-model mapping check

After terminal-suffix normalization, the official EPA API was queried for Samsung
`model_number=RF23D*9600**`. It returned one row: PD_ID `2839420`, the known
model pattern, four UPCs, and `markets=United States, Canada`.

The EPA pattern positionally includes `RF23DB9600QL`; with the approved terminal
suffix normalization, it also covers the observed exact SKU `RF23DB9600QLAA`.
This is the supported model-pattern inclusion observation for this pair. The
response did not contain `additional_model_information`, which only means EPA
did not also provide a separate explicit SKU list in that field. UPC values and
market text remain separate source observations. D09 remains open for current
status and US applicability; those questions are not answered merely by a
pattern match or the market text.

Offline report v3 implements the approved pattern inclusion observation as a
separate `model_pattern_inclusion` field. It records `INCLUDED` for the RF23
exact SKU after the approved suffix normalization. `NOT_INCLUDED` means only
that a SKU does not fit this one saved EPA pattern; it is not an exhaustive
EPA search or an uncertified finding. Current certification, US applicability
and assessment retain independent `NOT_EVALUATED` states. The report now reads
the saved actual EPA fixture rather than hardcoding its pattern, retaining
PD_ID and the original response body hash as references. This reference is not
a fresh API capture or a verification of the original bytes by the fixture test.
Hosted offline CI uploads the report for each Python version without networking
to Samsung or EPA.
