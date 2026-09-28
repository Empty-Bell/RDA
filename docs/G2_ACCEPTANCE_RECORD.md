# Phase 2 / G2 refrigerator acceptance — PASS, 2026-09-28

**Accepted scope:** the current US Samsung refrigerator population and the
approved ENERGY STAR publication, EnergyGuide numeric, and EnergyGuide model
identity controls. This is an audit execution and evidence gate. It does not
declare any product legally compliant or resolve future, unobserved source
error and unreadable-label severity policies.

The final code is `5c1553fbab1fdf1a8ab0f4d24d9e04a2ded12fbc` on `main`.
The [hosted G2 run](https://github.com/Empty-Bell/RDA/actions/runs/36376187192)
completed successfully on `ubuntu-24.04` after 155 G2 regression tests passed.
Its preserved [artifact](https://github.com/Empty-Bell/RDA/actions/runs/36376187192/artifacts/10952185823)
has SHA-256 `1b4db5b048c577d9cb43967b9b2c6db22bbd72d4428d70dc63fba9f64483931b`
and is retained through 2026-10-12 UTC.

The independent [acceptance replay](https://github.com/Empty-Bell/RDA/actions/runs/36378375953)
passed after downloading that same artifact. It checked every stored raw
evidence hash, canonical bundle validity, report source replay, dashboard
exports and finding evidence. Its result reports 75 exact SKUs, 36 findings,
FTC 75/75 and EPA 75/75 evaluated, EnergyGuide model 75/75 evaluated,
`phase_readiness=READY_FOR_FORMAL_REVIEW`, and zero readiness gaps. The
[acceptance result artifact](https://github.com/Empty-Bell/RDA/actions/runs/36378375953/artifacts/10951768009)
has SHA-256 `3460205a424fd6f10b18fde7cd545389ece99401262a30bf82231a6d1beda2d1`.
The separate [EnergyGuide quality review](https://github.com/Empty-Bell/RDA/actions/runs/36378375934)
also passed against the same source run. G1 CI passed on the same commit in
[run 36376187141](https://github.com/Empty-Bell/RDA/actions/runs/36376187141).

The canonical bundle version `G2_REFRIGERATOR_APPROVED_CONTROLS_V1` stores
227 per-control assessments and the same 36 findings represented in the
dashboard. The three controls retain independent FTC/EPA outcomes and raw
PDP, label, PLP and EPA Current Model Index references. The dashboard's
`compliance_gate` and every assessment's
`automatic_final_legal_conclusion` remain `NOT_EVALUATED` / `false`.

The earlier failed run 36369246125 and canceled run from the intermediate
formatting commit are retained as failure history. Wrong-model PDP redirects
remain an explicit early source gate; a future redirect, missing source,
unresolved model token or incomplete EPA scan cannot become a PASS. Policies
for unreadable documents, OCR corroboration under conflicting evidence and
source-wide HTTP failures remain open in `DECISIONS.md` (D07/D10) for future
occurrences. They were not needed to classify any model in this accepted run.

Phase 3/4 other-family acceptance, cross-family history and automatic
full-dashboard refresh remain separate work.
