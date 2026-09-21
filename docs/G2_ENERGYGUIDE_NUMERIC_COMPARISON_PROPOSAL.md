# G2 refrigerator EnergyGuide numeric comparison proposal

Status: three-source observation and approved numeric assessment implementation complete.

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

| Exact SKU | PDP | EnergyGuide | EPA | PDP − label |
|---|---:|---:|---:|---:|
| RF23DB990012AA | 22.8 | 22.5 | 22.5 | 0.3 |
| RF23DB9900QDAA | 22.8 | 22.5 | 22.5 | 0.3 |
| RF25C5551SR/AA | 25.0 | 24.5 | 24.5 | 0.5 |
| RF29DB990012AA | 29.0 | 28.6 | 28.6 | 0.4 |
| RF29DB9900QDAA | 29.0 | 28.6 | 28.6 | 0.4 |
| RS22T5561SR/AA | 22.0 | 21.5 | 21.5 | 0.5 |
| RS23CB7600QLAA | 23.0 | 22.6 | 22.6 | 0.4 |

The EPA refrigerator family rows for these seven products exactly corroborate the
EnergyGuide capacity and annual-energy values. The comparison uses only PD_IDs
already matched in the same-run Current Model Index binding. `p5st-her9` does not
become a certification source and does not change an ENERGY STAR assessment.
The official Current Model Index `8wj2-sec8` schema has 14 identity/status fields
and exposes neither annual energy nor capacity; these measurements therefore must
come from the product-family dataset when numeric corroboration is required.

Across the full population, EnergyGuide and EPA are exactly equal for all 48
comparable annual-energy rows and all 51 comparable capacity rows. Nineteen SKUs
have no Current Index candidate. Five matched Current Index rows are absent from
the refrigerator family response. Three SKUs have two same-pattern PD_IDs with
different annual-energy values; those annual values remain conflicting rather
than being selected from the label. Their common capacity remains usable.

## User-approved direction

1. Compare annual energy only when both sources provide numeric kWh/year.
2. Exact equality gives the annual-energy consistency subcontrol `PASS`.
3. Missing PDP annual energy is a LOW finding, at the same UI severity as the
   ENERGY STAR consistency improvement finding. It does not erase the independently
   collected label or EPA value.
4. Capacity uses exact equality with no tolerance. The seven observed differences
   are PDP-side inconsistencies because EnergyGuide and EPA agree exactly. Each
   confirmed capacity difference is a MEDIUM finding.
5. Numeric EPA enrichment is corroboration only. Current Model Index remains the
   sole EPA certification source.

The approved issue codes are `PDP_ANNUAL_ENERGY_MISSING` (LOW) and
`PDP_ENERGYGUIDE_CAPACITY_MISMATCH` (MEDIUM). The full 75-SKU assessment emits
31 findings across 29 affected SKUs: 24 LOW and seven MEDIUM. Two SKUs retain
both findings and display MEDIUM. UI counts are 46 PASS, seven MEDIUM and 22 LOW.
Document presence/accessibility and model identity remain independent controls.
Pipeline errors remain errors, and no missing comparison value becomes PASS.

Hosted ubuntu-24.04 assessment run 35564685897 passed at `8a6dcaf`; artifact
`g2-label-quality-35564685897-1` (ID 10624030788) contains the raw EPA numeric
capture, comparison and assessed JSON/Markdown. Common-contract regression run
35564685890 also passed at the same commit.
