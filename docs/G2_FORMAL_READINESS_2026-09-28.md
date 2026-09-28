# G2 refrigerator formal acceptance readiness — 2026-09-28

## Final hosted result — G2 PASS for approved refrigerator scope

[Hosted run 36376187192](https://github.com/Empty-Bell/RDA/actions/runs/36376187192)
and [acceptance replay 36378375953](https://github.com/Empty-Bell/RDA/actions/runs/36378375953)
passed at `5c1553f`. The downloaded artifact digest was verified and its
canonical bundle inspected directly: 75 products, 150 PDP/label facts,
227 assessed control records, 36 findings (14 HIGH, seven MEDIUM, 15 LOW),
32 affected SKUs, and 1,501 evidence records. FTC and EPA each cover all
75 SKUs; the label model control covers all 75. Acceptance readiness has zero
gaps. The [EnergyGuide quality review](https://github.com/Empty-Bell/RDA/actions/runs/36378375934)
also passed. [G2_ACCEPTANCE_RECORD.md](G2_ACCEPTANCE_RECORD.md) is the formal
scope and evidence record. Historical blocked sections below are retained as
the sequence leading to the final run.

## Canonical control activation — pending hosted execution

The three previously approved refrigerator controls now write versioned canonical
assessment records for every exact SKU: EPA ENERGY STAR publication, FTC
EnergyGuide numeric, and FTC EnergyGuide model-prefix inclusion. Each EPA
assessment cites the same-run raw Current Model Index pages; each FTC assessment
cites the same-run PDP and label evidence. A source error or unresolved control
stops the run before the canonical manifest can claim `SUCCESS`. Product-level
legal compliance remains `NOT_EVALUATED`.

An offline replay using the successful 75-SKU artifact from run 36371823748
produced 227 canonical assessments, including 36 findings across 32 SKUs. The
new report and dashboard replay passed with 75/75 FTC and EPA domain coverage,
75/75 label-model coverage, and no readiness gaps. This checks the integration
against saved evidence; a fresh hosted run and its acceptance replay remain
necessary before recording formal G2 acceptance.

## Resolved live rerun — 36371823748

At commit `5ed39d9`, [pilot run 36371823748](https://github.com/Empty-Bell/RDA/actions/runs/36371823748) succeeded. Its preserved artifact (ID 10950421626) confirms all 75 exact SKUs passed PDP identity, including both early watched SKUs at their original exact-model URLs. The full EnergyGuide model-prefix control reports 75 PASS, zero NOT_EVALUATED. The numeric control reports 59 PASS, seven MEDIUM and nine LOW display outcomes. The joined control summary retains 36 findings across 32 SKUs (14 HIGH, seven MEDIUM, 15 LOW).

[Acceptance replay 36373795904](https://github.com/Empty-Bell/RDA/actions/runs/36373795904) and [EnergyGuide quality review 36373795963](https://github.com/Empty-Bell/RDA/actions/runs/36373795963) also succeeded. Acceptance replay verifies 75 exact SKUs and 36 findings; phase readiness remains `BLOCKED` solely because the canonical FTC/EPA assessment engine is disabled (0/75 for each domain) and the canonical bundle is `PARTIAL`. The live redirect failure in the preceding run was intermittent at the observed times; the early watch remains in place for recurrence.

## New live source incident — run 36369246125

[Run 36369246125](https://github.com/Empty-Bell/RDA/actions/runs/36369246125)
failed after about 29 minutes. The preserved artifact
`g2-pilot-36369246125-1` (ID 10948868293) shows 75/75 PDP attempts,
73 exact identities and two failures:

| Requested exact SKU | Live final PDP SKU | Observation |
|---|---|---|
| `RF90F23BECRAA` | `RF90F29BECRAA` | 23-cu.ft. request redirected to 29-cu.ft. product |
| `RF90F29AEWAA` | `RF90F29AECRAA` | White-glass request redirected to another color |

Both SKUs remain in the 75-SKU PF grouped population but are not separate
rendered PLP cards in this capture. The preceding successful pilot had verified
both exact PDP URLs; this is a changed Samsung source response. Their saved
redirected pages contain another SKU's current page identity, so neither is
eligible for a PASS or for borrowing the destination model's facts. No source
scope change or new compliance issue code is inferred. The originally reported
`Comparison inputs do not cover the exact-SKU population` was a late secondary
error after these two PDP failures. The collector now writes PDP coverage and
stops before EPA/label OCR when any exact PDP identity fails, reporting the
requested SKU and final redirect URL in the checkpoint.
The two source-observed SKUs are also checked in a small early PDP preflight
while they remain in the live PF population. A repeat redirect now stops before
the other PDP visits; a successful preflight still requires the ordinary full
collection and exact identity gate. This watch does not exclude products or
alter a regulatory result.

## Source and result

Latest successful hosted refrigerator pilot: [run 36357733075](https://github.com/Empty-Bell/RDA/actions/runs/36357733075), commit `4ca94072`, artifact `g2-pilot-36357733075-1` (ID 10945720032), bundle run ID `52b6584e4c1244928eb2d057affd14fb`. Its saved report/dashboard replay passed [run 36359469658](https://github.com/Empty-Bell/RDA/actions/runs/36359469658). The replay proves artifact consistency, not G2 phase acceptance.

The downloaded artifact was replayed locally against the acceptance validator. It contains 75 exact refrigerator SKUs, 75 verified PDP identities, 75 selected label annual-energy values and capacities, 75 ENERGY STAR publication results, 75 numeric results, and 36 control findings across 32 SKUs (14 HIGH, 7 MEDIUM, 15 LOW). The label model-pattern assessment covers six reviewed SKUs. The canonical bundle contains only two `NOT_EVALUATED` domain assessment placeholders for one sample SKU; its execution status is `PARTIAL`, assessment is disabled, and `phase_gate` is `NOT_EVALUATED`.

The acceptance validator now reports an explicit `phase_readiness` alongside artifact replay `PASS`. For this saved run it reports `BLOCKED`: canonical execution incomplete, canonical assessment disabled, FTC evaluated 0/75, EPA evaluated 0/75, and EnergyGuide model assessment 6/75. `READY_FOR_FORMAL_REVIEW`, when eventually reported, will mean only these minimum completeness checks passed. Formal phase acceptance also requires the full reviewed control matrix and hosted evidence; it cannot be inferred from this field alone.

Subsequent user approval resolved the abbreviated-prefix question. The model
assessment now reads all printed model tokens separated by line breaks, commas
or semicolons and accepts any token that agrees with the beginning of the
normalized PDP identifier. Offline replay of the saved 75-SKU artifact yields
75 PASS and zero NOT_EVALUATED. This is a new control-level result, pending a
fresh hosted pilot; the older artifact and readiness result above remain
historically accurate. Canonical FTC/EPA assessment is still disabled.

## Remaining work in order

1. **EnergyGuide model coverage:** select every printed model token in each eligible PDF, including multiple lines and comma/semicolon lists. Compare the exact PDP SKU against all tokens using only approved suffix and wildcard rules. One matching token passes this control. Preserve source text, PDF hash, every token, and match evidence. Short family-only strings and unclear OCR need an explicit identity policy or reviewed source evidence; they must not be silently treated as mismatches or passes.
2. **Canonical FTC/EPA assessments:** connect already-approved ENERGY STAR publication and PDP/EnergyGuide numeric control results to the versioned canonical assessment records for every SKU. Add the remaining applicable EnergyGuide document/model/OCR checks after their rule boundaries are settled. Preserve separate domain findings and do not make an automated final legal conclusion.
3. **End-to-end acceptance:** run the full refrigerator job on hosted Ubuntu, replay evidence hashes, control coverage, report counts, dashboard exports, same-run provenance, and failure boundaries. Only then consider setting the G2 phase gate to PASS.

## Decisions needed before completing rule activation

- **Label model identity: resolved.** The user approved prefix matching; `RF18A5101` now matches `RF18A5101SR/AA` after the approved suffix normalization.
- **FTC label/document rule boundaries:** The latest 75-SKU corpus has no remaining model-inclusion uncertainty under the approved prefix rule, so no decision on an unmatched label is needed for this run. A future valid but unmatched or unreadable label will need a separately approved severity rule before it becomes a product finding. A technical collection failure remains a pipeline failure, not a product `PASS`.

No new issue code or severity is inferred in this readiness review.
