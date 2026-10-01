# Dashboard population review — 2026-09-28

## Result

The published Run #15 is a reviewed multi-run snapshot, not a current same-run audit. Its 557 `(product group, exact SKU)` keys match the selected source population keys for all 11 families. No duplicate keys, missing source SKUs, or extra published SKUs were found. All 557 records have one PASS/HIGH/MEDIUM/LOW grade, a PDP URL, and a model evidence file.

| Family | Selected source SKUs | Published SKUs | Set difference |
|---|---:|---:|---:|
| Refrigerator | 75 | 75 | 0 |
| Dishwasher | 21 | 21 | 0 |
| Clothes washer | 37 | 37 | 0 |
| Range | 58 | 58 | 0 |
| Cooktop | 20 | 20 | 0 |
| Clothes dryer | 54 | 54 | 0 |
| Hood | 16 | 16 | 0 |
| Monitor | 76 | 76 | 0 |
| Computer | 24 | 24 | 0 |
| TV | 165 | 165 | 0 |
| Tablet | 11 | 11 | 0 |
| **Total** | **557** | **557** | **0** |

## Apparent count differences

This section records the 2026-09-28 snapshot. The 2026-10-01 user decision
supersedes its population rule: every family now includes only exact SKUs on
rendered PLP product cards; hidden PF grouped variants are source context, and
TV `MNA` cards are no longer excluded by model prefix.

- **Tablet:** The source PF page records 50 grouped exact SKUs across 11 groups. The approved audit population is the 11 exact SKUs actually rendered on PLP cards; the other 39 grouped options are retained as source observations, not separately graded products. The four shards of [collection run 36294491520](https://github.com/Empty-Bell/RDA/actions/runs/36294491520) contain 11 unique `PLP_RENDERED_CARD` products, exactly matching all 11 published Tablet keys. This follows [TABLET_SOURCE_CONTRACT.md](TABLET_SOURCE_CONTRACT.md), which also keeps a rendered card in scope if its PDP redirects until exact PDP identity is resolved. [Tablet assessment run 36294606864](https://github.com/Empty-Bell/RDA/actions/runs/36294606864) grades those 11.
- **TV:** The PF source had 167 exact SKUs. The documented TV business scope excludes the two `MNA` SKUs `MNA101MS1BCXZA` and `MNA89MS1BACXZA`, leaving 165. The 165 published keys exactly match the post-exclusion collection. See [TV_SOURCE_CONTRACT.md](TV_SOURCE_CONTRACT.md) and [collection run 35703343706](https://github.com/Empty-Bell/RDA/actions/runs/35703343706).

## Method and boundary

The published `docs/model-data.json` keys were compared by set, not by count alone, against the saved per-family `products.json` collections; Refrigerator used the 75 exact declarations in its saved source manifest and TV used the post-exclusion collection. The Tablet check also verified every selected source product's `listing.sku_role` is `PLP_RENDERED_CARD`. Family and total counts, unique keys, grades, PDP URLs, and evidence-file references were checked separately.

This verifies **published snapshot vs. saved source population**. It does not establish that Samsung's live PLPs still have the same population on 2026-09-28, that different family runs form one coherent audit run, or that G2–G4 formal acceptance is complete. Those remain separate operational gates under [MASTER_PLAN.md](MASTER_PLAN.md).
