# Remaining refrigerator ENERGY STAR HIGH diagnosis

## Result

The corrected run leaves 14 HIGH SKU findings, but they are only eight Samsung
source product groups. This is not evidence of fourteen independent defects.

| Samsung source group | Exact SKU count | Exact SKUs | Current Index diagnostic |
|---|---:|---|---|
| MULTI_GROUP_ID_601343 | 3 | RF70H25GERAA, RF70H30GEEAA, RF70H30GERAA | No `RF70H` row anywhere; closest rows begin `RF70F` |
| MULTI_GROUP_ID_601347 | 2 | RF70H25HERAA, RF70H30HERAA | No `RF70H` row anywhere; closest rows begin `RF70F` |
| MULTI_GROUP_ID_601349 | 3 | RF70H25KERAA, RF70H30KEEAA, RF70H30KERAA | No `RF70H` row anywhere; closest rows begin `RF70F` |
| MULTI_GROUP_ID_601365 | 2 | RF27CG5B30SRAA, RF32CG5B30SRAA | `RF27CG5B10**` and `RF32CG5B10**` exist, but their fixed positions differ (`1` is not `3`) |
| MULTI_GROUP_ID_601367 | 1 | RF25C5A01SRAA | Closest rows are `RF25C5151**` and `RF25C5551**`; no direct candidate |
| MULTI_GROUP_ID_601379 | 1 | RF32CG5D00SRAA | No `RF32CG5D` row |
| MULTI_GROUP_ID_601364 | 1 | RF80H30CERAA | No `RF80H` row |
| MULTI_GROUP_ID_601363 | 1 | RZ40H11PETAA | No `RZ40H` row |

## What was ruled out

- The approved terminal `AA` and `/AA` normalization is applied before
  comparison.
- EPA `*` now matches one alphanumeric position; `#` remains one digit-only
  position. The correction removed ten false HIGH candidates.
- Every remaining target was searched against every field of every Samsung row
  in the same complete Current Model Index snapshot, including
  `additional_model_information`; there is no hidden exact source identifier
  for these target strings.
- The Samsung Bridge source identifies the same exact `modelCode` used in the
  target SKU. No alternate official Samsung certification identifier was found
  in the captured exact-SKU source declaration.

## What the current index says

The captured Current Model Index metadata reports a row update on 2026-09-20,
but the newest Samsung refrigeration certification date in its 118
refrigeration rows is 2025-09-19. Its latest `RF70` entries are `RF70F...`;
there are no `RF70H`, `RF80H`, or `RZ40H` entries. This supports a current-list
generation gap as a plausible explanation, but does not establish why it
exists. The audit must not turn a near-prefix into a certified match.

## Operational interpretation

Keep the 14 exact-SKU HIGH findings under the approved rule, but present them
to reviewers as eight source-family clusters. The next useful verification is
to ask whether these eight Samsung product groups should have a matching
current EPA model-pattern record; it should not loosen fixed-position matching
or infer that nearby `F` or `...B10...` models cover a different `H` or
`...B30...` code.
