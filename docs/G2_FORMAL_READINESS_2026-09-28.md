# G2 refrigerator formal acceptance readiness — 2026-09-28

## Source and result

Latest successful hosted refrigerator pilot: [run 36357733075](https://github.com/Empty-Bell/RDA/actions/runs/36357733075), commit `4ca94072`, artifact `g2-pilot-36357733075-1` (ID 10945720032), bundle run ID `52b6584e4c1244928eb2d057affd14fb`. Its saved report/dashboard replay passed [run 36359469658](https://github.com/Empty-Bell/RDA/actions/runs/36359469658). The replay proves artifact consistency, not G2 phase acceptance.

The downloaded artifact was replayed locally against the acceptance validator. It contains 75 exact refrigerator SKUs, 75 verified PDP identities, 75 selected label annual-energy values and capacities, 75 ENERGY STAR publication results, 75 numeric results, and 36 control findings across 32 SKUs (14 HIGH, 7 MEDIUM, 15 LOW). The label model-pattern assessment covers six reviewed SKUs. The canonical bundle contains only two `NOT_EVALUATED` domain assessment placeholders for one sample SKU; its execution status is `PARTIAL`, assessment is disabled, and `phase_gate` is `NOT_EVALUATED`.

The acceptance validator now reports an explicit `phase_readiness` alongside artifact replay `PASS`. For this saved run it reports `BLOCKED`: canonical execution incomplete, canonical assessment disabled, FTC evaluated 0/75, EPA evaluated 0/75, and EnergyGuide model assessment 6/75. `READY_FOR_FORMAL_REVIEW`, when eventually reported, will mean only these minimum completeness checks passed. Formal phase acceptance also requires the full reviewed control matrix and hosted evidence; it cannot be inferred from this field alone.

## Remaining work in order

1. **EnergyGuide model coverage:** select every printed model token in each eligible PDF, including multiple lines and comma/semicolon lists. Compare the exact PDP SKU against all tokens using only approved suffix and wildcard rules. One matching token passes this control. Preserve source text, PDF hash, every token, and match evidence. Short family-only strings and unclear OCR need an explicit identity policy or reviewed source evidence; they must not be silently treated as mismatches or passes.
2. **Canonical FTC/EPA assessments:** connect already-approved ENERGY STAR publication and PDP/EnergyGuide numeric control results to the versioned canonical assessment records for every SKU. Add the remaining applicable EnergyGuide document/model/OCR checks after their rule boundaries are settled. Preserve separate domain findings and do not make an automated final legal conclusion.
3. **End-to-end acceptance:** run the full refrigerator job on hosted Ubuntu, replay evidence hashes, control coverage, report counts, dashboard exports, same-run provenance, and failure boundaries. Only then consider setting the G2 phase gate to PASS.

## Decisions needed before completing rule activation

- **Label model identity:** A label sometimes prints only a shortened family identifier, such as `RF18A5101`, while the PDP exact SKU is `RF18A5101SR/AA`. Should this count as a model match, or remain unresolved until the label or Samsung supplies an explicit variant mapping? The already-approved rule that *any one of multiple printed models may match* does not by itself define this shorter-identifier case.
- **FTC label/document rule boundaries:** Confirm whether a PDF that is valid and has selected annual energy/capacity but has no resolved exact-SKU model link should be a `MEDIUM`/`HIGH` finding or remain unevaluated pending identity review. A technical collection failure remains a pipeline failure, not a product `PASS`.

No new issue code or severity is inferred in this readiness review.
