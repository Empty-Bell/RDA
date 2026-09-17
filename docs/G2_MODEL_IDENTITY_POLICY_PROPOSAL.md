# G2 model interpretation and identity policy proposal

Status: DRAFT / awaiting user semantic approval. D07 and D09 remain OPEN.
Scope: refrigerator fixtures first; no live correction, EPA matching, rule,
severity or new issue code is enabled by this document.

## Recommended decision

Approve a conservative evidence contract for fixture-only implementation:
1. Keep raw OCR, reviewed visual transcription, and product identity decisions
   as separate records. A transcription does not populate
   `label_model_normalized` or `model_confusion_corrected`.
2. Withhold wildcard/suffix identity until an explicit source-backed mapping
   contract exists. No default glob, prefix, suffix stripping or character
   substitution is permitted.
3. Record literal equality as a diagnostic only. It does not establish current
   US certification, label applicability or a compliance PASS.

Approval authorizes only the fixture evidence contract and its hosted tests.
Live interpretation and substantive matching require their own acceptance.

## Interpretation evidence

Preserve the original PDF, SHA256, raw extraction, full model descriptor and
token, extraction engine/settings, page, model region coordinates, and render
hash before proposing an interpretation. Keep review annotations separate from
source facts, with reviewer identifier, UTC review time, annotation version,
reviewed PDF/render hashes, page/region, and proposed transcription.

A visual review may confirm what is printed on the preserved image. It is not
independent product-identity corroboration. Repeated OCR, another render of the
same PDF, a filename, or a matching URL also does not supply that corroboration.
The existing saved annotations remain historical observations; missing new
review metadata must be reported, never fabricated or silently backfilled.

Changed PDF bytes invalidate the prior interpretation binding. Multiple model
regions, an unclear glyph, unknown wildcard count, incomplete page/panel review,
or conflicting annotations withhold an accepted transcription. Explicit review
rejection is separate from a runtime failure; malformed evidence fails the job.

## Matching boundaries

| Evidence condition | Proposed diagnostic behavior | What it cannot conclude |
|---|---|---|
| Full model strings literally equal, no wildcards, complete context | Record literal equality and evidence references | Correct label, current certification or US-market applicability |
| Wildcard in either string, including a repeated star | Withhold identity interpretation | Star width, allowed characters or covered SKU set |
| Raw token has no star but review shows missing/substituted glyphs | Preserve discrepancy; require review | Wildcard-free identity from raw token |
| Strings differ only in suffix, `/AA`, `AA`, case or punctuation | Preserve both strings; withhold equivalence | Automatic canonicalization |
| One plausible B/8, O/0, I/l/1 or S/5 confusion | Preserve a proposed interpretation only | Automatic replacement or genuine wrong-model finding |
| Different model lengths, several ambiguities or conflicting source values | Withhold correction and identity | Choosing whichever candidate best fits the target |
| Incomplete EPA query, parser/access failure or unresolved routing | Record failure/unknown query scope | No certification candidate |

Literal inequality is also diagnostic only: unresolved extraction or a family
descriptor must not become a wrong-model finding.

A future wildcard contract must identify its issuing source, dataset/product
scope, pattern grammar, each wildcard's width and permitted characters, suffix
meaning, effective version, and explicit ambiguity handling. A source-declared
finite SKU list may support a reviewed mapping, but existing `exact_skus` in
collection annotations means only where the PDF was retrieved. It is not a
manufacturer declaration that the PDF covers those products.

## Deferred automatic correction (D07)

No confidence threshold is supported by the five reviewed PDFs. RF18A5101 loses
stars at confidence 0.9941; RF22A4111 substitutes a quote at 0.97118.
`RF23D*9600**` agrees with the visible descriptor but its wildcard semantics
still remain unknown. The sample cannot validate a general correction policy.

Automatic confusion correction remains blocked until D01 defines comparable
energy/capacity test bases and tolerances, D09 defines independent EPA identity,
and D07 approves the required corroboration matrix and contradiction precedence.
The policy must not use an EPA row selected by the proposed correction to prove
that same correction. Numeric agreement alone cannot resolve wildcard meaning.

## Verification milestones after approval

| Milestone | Deliverable | Verification | Model recommendation |
|---|---|---|---|
| M1 | Separate review-evidence fixture contract | Original token unchanged; missing reviewer/hash/region rejected; changed bytes and conflicting reviews withheld | Luna low |
| M2 | Diagnostic identity fixtures | Exact equality stays diagnostic; wildcard, suffix, missing-star and confusion cases withhold equivalence; no assessments created | Luna low |
| M3 | Hosted offline checkpoint | Existing cheap G2 workflow on ubuntu-24.04, Python 3.11/3.12; artifact and commit recorded | Luna low |
| M4 | Independent matching/corroboration proposal | Source-backed grammar and non-circular evidence matrix; D01/D07/D09 decisions reviewed before implementation | Sol medium |

No live collector rerun is needed for M1–M3. Audit runtime uses deterministic
Python and no LLM calls. This draft is a review deliverable, not a hosted G2
acceptance or decision closure. Existing live checkpoint 35184128593 remains
source-observation evidence only.
