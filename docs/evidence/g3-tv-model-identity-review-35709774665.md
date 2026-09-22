# TV model-identity review — run 35709774665

Workflow: [G3 television PDP label EPA source comparison candidates](https://github.com/Empty-Bell/RDA/actions/runs/35709774665)  
Machine-readable same-run output: [comparison artifact](https://github.com/Empty-Bell/RDA/actions/runs/35709774665/artifacts/10685969906)  
Source capture: [EnergyGuide and EPA Current artifacts](https://github.com/Empty-Bell/RDA/actions/runs/35704704116)

This run applies the TV model-identity-only scope. PDP annual-energy values, label annual-energy values, EPA annual-energy values, and PDP power values are not compared or emitted as comparison results.

## Population result

| Check | Result | Meaning |
|---|---:|---|
| Exact PDP SKU identity verified | 165 / 165 | PDP collection identifies the exact Samsung SKU. |
| Readable label model patterns matched to the SKU | 160 / 160 | Every readable EnergyGuide model pattern matched the corresponding SKU under the approved positional-prefix rule. |
| EPA Current US model-pattern matches | 35 / 165 | Current EPA rows matched 35 SKUs under the same positional-prefix rule and list the United States market. |
| No exact current EPA model-pattern match | 130 / 165 | EPA Current has no exact model-pattern row for these SKUs in this capture. This alone is not evidence that the PDP or label model name is wrong. |
| EnergyGuide not accessible | 5 / 165 | Samsung's document endpoint returned NASCA DRM; model text could not be checked from those PDFs. These remain HIGH accessibility candidates. |
| Readable label model-pattern mismatches | 0 / 160 | No mismatch was observed among readable labels. |

The 130 EPA no-match cases consist of 125 SKUs with a readable, SKU-matching EnergyGuide model pattern and 5 SKUs whose EnergyGuide PDF was inaccessible. The run found 59 diagnostic “near EPA pattern” suggestions among the no-match group; these are prefix-similarity suggestions only and are not accepted matches.

## EnergyGuide PDFs that could not be read

All five PDP identities are verified. The source PDFs return Samsung NASCA DRM, so their printed model patterns remain unverified:

| SKU | Source EnergyGuide PDF |
|---|---|
| QN55LS03HEFXZA | [Open PDF](https://images.samsung.com/is/content/samsung/p6pim/us/qn55ls03hefxza/energyguide/us-energyguide-qn55ls03hefxza-552228699.pdf) |
| QN65LS03HEFXZA | [Open PDF](https://images.samsung.com/is/content/samsung/p6pim/us/qn65ls03hefxza/energyguide/us-energyguide-qn65ls03hefxza-552228697.pdf) |
| QN75LS03HEFXZA | [Open PDF](https://images.samsung.com/is/content/samsung/p6pim/us/qn75ls03hefxza/energyguide/us-energyguide-qn75ls03hefxza-552228523.pdf) |
| QN85LS03HEFXZA | [Open PDF](https://images.samsung.com/is/content/samsung/p6pim/us/qn85ls03hefxza/energyguide/us-energyguide-qn85ls03hefxza-552228521.pdf) |
| QN98LS03HEFXZA | [Open PDF](https://images.samsung.com/is/content/samsung/p6pim/us/qn98ls03hefxza/energyguide/us-energyguide-qn98ls03hefxza-552228520.pdf) |

## Interpretation for the next decision

The current evidence supports three separate outcomes: exact model identity verified across PDP, label, and EPA (35); PDP/label model identity verified but no matching EPA Current row found (125); and PDP identity verified while the label remains unreadable (5). Do not turn an EPA no-row result or a near-pattern suggestion into a model-name mismatch automatically. Any rule that treats EPA absence as a certification or ENERGY STAR logo issue belongs to the separate eligibility/publication control.
