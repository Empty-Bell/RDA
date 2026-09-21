# G2 refrigerator EnergyGuide numeric comparison proposal

Status: observation implementation complete; finding policy awaiting approval.

## Full-population observation

The current 75-SKU refrigerator artifact and the completed label-selection replay
produce the following exact-SKU comparison. No tolerance or finding is applied.

| Field | Equal | Different | Not comparable |
|---|---:|---:|---:|
| Annual energy (kWh/year) | 51 | 0 | 24 |
| Capacity (cu ft) | 62 | 7 | 6 |

All 51 SKUs that expose PDP annual energy exactly equal the selected EnergyGuide
annual value. The 24 non-comparable rows have no PDP annual-energy observation;
their label values are present. Missing PDP energy is not currently an approved
finding.

The seven capacity differences are 0.3–0.5 cu ft:

| Exact SKU | PDP | EnergyGuide | PDP − label |
|---|---:|---:|---:|
| RF23DB990012AA | 22.8 | 22.5 | 0.3 |
| RF23DB9900QDAA | 22.8 | 22.5 | 0.3 |
| RF25C5551SR/AA | 25.0 | 24.5 | 0.5 |
| RF29DB990012AA | 29.0 | 28.6 | 0.4 |
| RF29DB9900QDAA | 29.0 | 28.6 | 0.4 |
| RS22T5561SR/AA | 22.0 | 21.5 | 0.5 |
| RS23CB7600QLAA | 23.0 | 22.6 | 0.4 |

The master plan already states that 29 PDP versus 28.6 label capacity is not an
identity failure or finding. The available data does not establish that every PDP
capacity label uses the same tested/net capacity definition as EnergyGuide.

## Recommended V1 policy requiring approval

1. Compare annual energy only when both sources provide numeric kWh/year.
2. Exact equality gives the annual-energy consistency subcontrol `PASS`.
3. Missing PDP annual energy gives `NOT_EVALUATED` for this subcontrol and no
   finding; it does not erase the independently collected label value.
4. A future numeric difference gives `MEDIUM` review finding
   `ENERGYGUIDE_ANNUAL_ENERGY_SOURCE_CONFLICT`. It does not automatically claim
   that the label, PDP or document is legally wrong.
5. Record capacity equality/difference for evidence only. Capacity does not emit
   a finding and does not corroborate model identity in V1.
6. No capacity tolerance is introduced. The raw difference is retained so a
   later measurement-basis decision can evaluate it without re-collecting data.

This policy is intentionally narrower than a whole EnergyGuide PASS. Document
presence/accessibility and model identity remain independent controls. Pipeline
errors remain errors, and no missing comparison value becomes PASS.
