# G3 television family control acceptance — PASS, 2026-09-28

**Accepted scope:** the current 165 US Samsung TV listing SKUs after the approved `MNA` exclusion, with exact PDP identity, printed EnergyGuide model inclusion, label document accessibility, and EPA Current/ENERGY STAR publication controls. TV annual-energy and power-value comparisons are outside this approved scope. This family-control result is not a legal compliance conclusion or G3-wide acceptance.

The hosted [source comparison](https://github.com/Empty-Bell/RDA/actions/runs/36401803388) binds collection `36292869106` and label/EPA capture `36292945283`. It verified all 165 PDP identities. All 158 readable EnergyGuide labels contain a model pattern matching the PDP SKU under the approved fixed-prefix rule; there are zero observed readable-label model mismatches. Five Samsung documents returned NASCA DRM and two SKUs had no Support-declared EnergyGuide document. The source comparison identifies 35 US-market EPA Current model matches and 130 no-match results; an EPA no-match alone is not a model-name mismatch.

The hosted [final assessment](https://github.com/Empty-Bell/RDA/actions/runs/36411631059) at commit `26bf4dac90022c81d35d5ca549dbcdfe523946f3` finished with `status: PASS`, zero readiness gaps, and **157 PASS, 8 HIGH, 0 MEDIUM, 0 LOW**. HIGH comprises five unreadable EnergyGuide files, two missing EnergyGuide documents, and `QN77S84FAEXZA`, which displays ENERGY STAR on both PLP and PDP despite no Current EPA model match.

`QN83S90DAEXZA` changed from the older dashboard HIGH to PASS. In the source-bound current collection, its PLP and PDP ENERGY STAR flags are both explicit `N`; the complete Specs inventory contains no ENERGY STAR certification field. The prior dashboard treated a Specs claim as present, but the accepted current evidence does not support that claim. Field absence is `NOT_APPLICABLE`, distinct from explicit `No`.

The assessment artifact is `10964417729`, SHA-256 `bb98ea34af4557080b0c7df9a4fbbd3d79f8e009acb4fe835845cae05491de58` (GitHub retention through 2026-10-12 UTC). It preserves per-SKU source facts and refuses formal PASS if PDP identity, label identity or availability, EPA Current state, or publication observation remains unresolved.

Mixed-family Pages snapshot Run #17 includes this accepted TV result and the accepted Washer result. It is a collection of family control runs, not one unified audit execution. G3 remains open for other families and integration.
