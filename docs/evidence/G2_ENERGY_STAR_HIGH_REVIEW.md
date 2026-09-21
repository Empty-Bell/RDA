# Refrigerator ENERGY STAR HIGH review table

## Scope and correction

This is the reviewer-facing HIGH extract after hosted run
[`35548351322`](https://github.com/Empty-Bell/RDA/actions/runs/35548351322)
successfully applied the corrected EPA pattern comparison. The preceding
24-row extract was superseded: the matcher had treated `*` as a letter-only
position. EPA rows such as `RF23BB8600**` demonstrate that `*` can also occupy
a digit position, so ten false HIGH candidates are now registered matches.

The remaining rows have the same HIGH trigger: the complete same-run EPA
Current Model Index `8wj2-sec8` Samsung scope found **no literal or approved
fixed-position-pattern candidate** for the normalized exact SKU, while Samsung
declares ENERGY STAR on PLP and PDP. This is an eligibility candidate for
review, not a conclusion that Samsung has made an unlawful claim. `Y` is the
exact-SKU affirmative source field; `Yes` is an affirmative Bridge Specs row;
`—` means no affirmative certification row was captured.

| # | Exact SKU | EPA Current Index | PLP | PDP | Bridge Spec | PDP for review |
|---:|---|---|:---:|:---:|---|---|
| 1 | RF25C5A01SRAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-25-cu-ft-3-door-french-door-refrigerator-with-auto-ice-maker-and-all-around-cooling-in-stainless-steel-sku-rf25c5a01sraa) |
| 2 | RF27CG5B30SRAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-26-cu-ft-mega-capacity-counter-depth-3-door-french-door-refrigerator-with-external-water-and-ice-dispenser-in-stainless-steel-sku-rf27cg5b30sraa) |
| 3 | RF32CG5B30SRAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-31-cu-ft-mega-capacity-counter-depth-3-door-french-door-refrigerator-with-external-water-and-ice-dispenser-in-stainless-steel-sku-rf32cg5b30sraa) |
| 4 | RF32CG5D00SRAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-32-cu-ft-mega-capacity-3-door-french-door-refrigerator-with-auto-ice-maker-in-stainless-steel-sku-rf32cg5d00sraa) |
| 5 | RF70H25GERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-24-cu-ft-counter-depth-3-door-french-door-refrigerator-with-zero-clearance-fit-and-sphere-ice-in-stainless-steel-sku-rf70h25geraa) |
| 6 | RF70H25HERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-24-cu-ft-counter-depth-3-door-french-door-refrigerator-with-zero-clearance-fit-and-dual-auto-ice-maker-in-stainless-steel-sku-rf70h25heraa) |
| 7 | RF70H25KERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-25-cu-ft-counter-depth-3-door-french-door-refrigerator-with-zero-clearance-fit-and-in-door-tall-water-dispenser-in-stainless-steel-sku-rf70h25keraa) |
| 8 | RF70H30GEEAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-29-cu-ft-3-door-french-door-refrigerator-with-zero-clearance-fit-and-sphere-ice-in-matte-black-steel-sku-rf70h30geeaa) |
| 9 | RF70H30GERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-29-cu-ft-3-door-french-door-refrigerator-with-zero-clearance-fit-and-sphere-ice-in-stainless-steel-sku-rf70h30geraa) |
| 10 | RF70H30HERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-29-cu-ft-3-door-french-door-refrigerator-with-zero-clearance-fit-and-dual-auto-ice-maker-in-stainless-steel-sku-rf70h30heraa) |
| 11 | RF70H30KEEAA | No candidate | Y | Y | — | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-30-cu-ft-3-door-french-door-refrigerator-with-zero-clearance-fit-and-in-door-tall-water-dispenser-in-matte-black-steel-sku-rf70h30keeaa) |
| 12 | RF70H30KERAA | No candidate | Y | Y | — | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-30-cu-ft-3-door-french-door-refrigerator-with-zero-clearance-fit-and-in-door-tall-water-dispenser-in-stainless-steel-sku-rf70h30keraa) |
| 13 | RF80H30CERAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/french-door/bespoke-ai-29-cu-ft-3-door-french-door-refrigerator-with-autoview-and-zero-clearance-fit-in-stainless-steel-sku-rf80h30ceraa) |
| 14 | RZ40H11PETAA | No candidate | Y | Y | ENERGY STAR® Certified: Yes | [Open](https://www.samsung.com/us/refrigerators/one-door/11-4-cu-ft-capacity-convertible-upright-freezer-in-stainless-look-sku-rz40h11petaa) |

## How to review one row

1. Open the PDP link and verify the product/SKU, ENERGY STAR presentation, and
   specs for that exact SKU.
2. In the hosted artifact, compare the recorded exact-SKU PF `energyStarFlg`,
   PDP Next `energyStarFlag`, and Bridge Specs ENERGY STAR rows.
3. Re-run the Current Model Index capture when a fresh EPA state is needed.
   A HIGH here is limited to the source snapshot captured in the cited run.
