# Clothes Dryer EPA-focused source reconnaissance

Status: bounded Clothes Dryer source reconnaissance PASS on hosted Ubuntu (35109208255).
Phase 0 remains RUNNING. Certification matching/compliance NOT_EVALUATED.

Official sources:
- Samsung listing: https://www.samsung.com/us/laundry/dryers/
- Catalog: https://catalog.data.gov/dataset/energy-star-certified-residential-clothes-dryers
- EPA metadata: https://data.energystar.gov/api/views/t9u7-4d2j.json
- EPA sample: https://data.energystar.gov/resource/t9u7-4d2j.json?$limit=3

Official metadata identifies t9u7-4d2j Certified Residential Clothes Dryers.
Preserve product_type, type (Fuel Type), drum_capacity_cu_ft, combined_energy_factor_cef,
estimated_annual_energy_use_kwh_yr and date_qualified (Date Certified) independently.
CEF is efficiency, not annual kWh. Fuel values and complete current-certification
applicability/matching require later evidence. Combo/stacked products must not be
forced into standalone dryer certification solely from listing membership.

Actual category/taxonomy/bridge IDs come from the live page requests. Terminal API
population and unique rendered tile groups must reconcile; retain exact variants.
Exact Specs/Support is probed; EnergyGuide PDF is OUT_OF_RECON_SCOPE in this EPA-only
reconnaissance. No legal applicability conclusion is made from that probe scope.
Cold hosted Ubuntu 24.04, version-matched desktop Chromium UA, no runtime LLM.
See SOURCE_COVERAGE.md: this is population discovery plus sample verification,
not full per-model PDP/label collection or EPA SKU lookup.

## First hosted observations

Run https://github.com/Empty-Bell/RDA/actions/runs/35108542847, commit bf2d77e.
Dryer source checks PASS. Actual pf_search category_code 08010000 with taxonomy_code
08010300, distinct from washer taxonomy 08010100. Offsets 0/14, request counts 14/16,
returned 14/5, terminal total 19 groups = 19 distinct rendered groups; 54 exact SKUs.
13 representative visible links are not a tile count. Snapshot counts are not constants.

First target WD90F53AVBUS is the combo also observed in the washer listing; bridge
group_id 569348. Keep cross-listing provenance and do not double-count it as two
different exact products in a future canonical population. Its source Energy Guide
Label 103 kWh/year describes Clothes Washer, not full wash-plus-dry energy. Raw
Specs/Support remain preserved but dryer annual-energy/capacity projection is UNKNOWN.
EnergyGuide metadata exists; PDF probe remains OUT_OF_RECON_SCOPE in this EPA task.

EPA t9u7-4d2j metadata has 35 columns. Generic sample LG DLGX3371*, Gas Standard
Vented, fuel Gas, drum 7.4 cu-ft, CEF 3.49, annual energy 685 kWh/yr. This is not a
Samsung candidate lookup. Gas energy/test-basis semantics must not be inferred from
the unit label alone. Full fuel/vented/heat-pump routing and matching remain open.

Initial dryer artifact 10451073435 (20640 bytes), ZIP SHA256
c4885fca61d696d32ea9fefaea006135f4895e413934de9fc377d72f1d1b6810.
The same run's refrigerator pagination FAIL detected duplicate/missing source groups;
failed artifact 10451058425 ZIP SHA256
81a3131a507930be4912dae141d96656634847a4d4e1fd65edb5a658e0cf20b1.
The source-health failure is retained, not deduplicated into a complete population.

## Additional standalone sample

Run 35108856923, commit 6ad110c94f08148354f52ee55be51369eb7a7d9a, dryer job
104837015196 source checks PASS. Sample DV90F53AESA3 exact Specs/Support uses
bridge group_id 570057. Drying Capacity (cu.ft) 7.6 cu.ft; Energy Star Certification
Yes (mixed-case source name). Claim collector was subsequently made case-insensitive
while preserving original names/values; a real fixture reproduces that prior omission.
No annual-energy spec inferred. PDP DOE Energy Factor 3.93 lb/kWh is retained only
as an uninterpreted Samsung raw spec, never used as audit input or substituted for
EPA CEF. DOE is not an input source under the master plan.

Full standalone gas/heat-pump/stacked product coverage and fuel/combination applicability
remain unverified. Only combo and one standalone sample PDP are probed. Neither
schema samples nor a Yes PDP claim establish current EPA certification.

## Final hosted validation

https://github.com/Empty-Bell/RDA/actions/runs/35109208255
Commit bb87f1aa2530a56d4327e8a88d245f76590dffa8, dryer job 104838211794.
71 tests, all five dryer source checks and artifact upload PASS. All seven product
group jobs in this final hosted run concluded success. Earlier refrigerator duplicate
pagination failure remains source-health evidence; this success does not prove stability.

Final dryer artifact 10452050631 (27276 bytes), ZIP SHA256
3720b0c6719f43f7a9e6794a03537807775478cefa87a853805b0bae20c54116.
Compact source observations: docs/evidence/dryer-source-recon.json; fixture hashes/
source run IDs: docs/evidence/dryer-fixture-manifest.json. Raw evidence expires 2026-09-30.
Next bounded group: Ventilating Hood. No LLM calls in hosted runtime. Source coverage
is population plus two sample PDPs and generic EPA sample, not per-model certification.

## G3 exact-SKU collection (2026-09-22)

Fresh hosted dryer source reconnaissance passed in run 35712517039. The new
exact-SKU PDP collection passed in run 35712660255: 54/54 verified exact
identities, zero failed and zero unattempted. It preserves raw exact-SKU
Specs/Support, independent ENERGY STAR claim channels, EnergyGuide document URLs,
browser identity and bridge/PF hashes. Washer-energy values found on a washer-dryer
combo PDP remain raw Specs only and are not projected as dryer annual energy.
An automatically duplicated collection run 35713169010 stopped at the source
artifact identity guard before attempting PDP pages; it does not invalidate the
complete earlier collection artifact.

EPA Current Samsung dryer cohort capture and exact-SKU Support PDF retrieval
passed in hosted run 35714849653. Capture included 104 Samsung rows from dataset
`t9u7-4d2j`; retrieval retained 54-SKU document coverage, 11 declared URLs, 5
unique valid PDF bodies. This is source capture only. Annual-energy field
selection, fuel/venting/combination routing, model matching and severity
assessment remain NOT_EVALUATED.

## EnergyGuide observation and raw review queue

New hosted-only workflows observe each unique PDF hash once, preserve extracted
text and page detections, OCR image-only pages (and supplement embedded text if
no annual-energy candidate appears), then emit a raw candidate index tied to exact
PDP SKU-document links. Dryer capacity candidates use the printed “Drying
Capacity (cu.ft)” line; annual-energy candidates require yearly-electricity
context. These are candidate heuristics only: no OCR correction, candidate
selection, wildcard matching, numeric comparison, pass/fail, or severity is
enabled. Combo washer energy is not projected as dryer energy. These steps run on
GitHub-hosted `ubuntu-24.04`, with the existing pinned OCR/PDF dependencies and no
LLM calls. Observation run 35715470080 PASSed and review queue run 35715542396
PASSed. Five unique PDFs cover 11 of the 54 PDP SKUs under the then-current
canonical-name-only Support projection; the remaining Support entries were not
preserved, so their label-link coverage is unknown. Four PDFs produced
annual-kWh candidates 94, 95, 103, and 103
with printed WD/WH model patterns. Keep these as raw evidence and do not project
them into dryer energy. The PDF linked to DV53BB8900HDA2 is valid but yielded no
model, annual-kWh, capacity, or US-heading candidate; retrieval did not fail. No
capacity candidate was extracted across the five documents. This is an extraction
observation, not proof that the original PDF visually lacks those elements; its
preview/source needs inspection before interpreting absence.

The same-run source candidate join is now implemented and waits on the review
artifact. It preserves literal PDP specs, label candidates, and EPA model/fuel/
venting/annual-energy/CEF/capacity row fields. Positional `*` inclusion is shown
only as an explicitly labeled candidate, retaining any exact-SKU suffix. No label
selection, numeric comparison, dryer/combo routing, pass/fail, or severity is
enabled. Hosted source-candidate join run 35716279708 PASSed against those same
artifacts. It retained all 54 exact SKUs and surfaced 28 SKU/EPA positional model
pattern candidates from the 104-row EPA source set. The count is candidate links,
not confirmed matches or findings. The full downloadable report includes EPA
annual energy, CEF, capacity, fuel/type, venting and market fields alongside PDP
and label records. Next: inspect these candidate rows and the DV53-linked PDF
preview/source; then define the Dryer source comparison gates before any numeric
comparison or assessment. Recommended model for routine fixed-schema run review:
GPT-5.6 Luna low; GPT-5.6 Terra medium only if a new source-policy decision is
needed.

## Combo component energy separation

EPA publishes a separate current dataset, `9jai-gs6t`, named `ENERGY STAR
Certified Res-Combo-Washer-Dryer`, for combination all-in-one washer/dryers. Its
schema names washer annual energy (`annual_energy_use_kwh_year`) and dryer-side
annual energy (`estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer`)
as separate quantities, with separate dryer capacity and CEF fields. The G3
combo capture preserves the complete Samsung cohort and source metadata; it does
not route SKUs, decide applicability, compare energy, or assess compliance. Do
not collapse these two energy fields or use the washer-side EnergyGuide value as
the dryer-side value.

The candidate-join Actions summary now reports label model text and annual-kWh
text in separate columns. Values found in one shared PDF are not presented as
paired model/value assertions unless a later, approved source rule establishes
that relationship. The first fresh hosted combo capture passed in run
`35717430123`: EPA returned three Samsung rows. Its artifact is hash-checked,
and the Actions summary prints washer and dryer energy in distinct columns. The
candidate join now adds combo rows to a separate SKU/model-pattern candidate
field and preserves both annual-energy values plus dryer CEF/capacity. Numeric
comparison and grading remain disabled pending source applicability review.

The automated follow-up comparison passed in run `35717939255` (21 seconds):
54 PDP SKUs, 104 ordinary Dryer EPA rows, and 3 EPA all-in-one combo rows.
The report exposes 6 WD53/WD90 exact-SKU links to the all-in-one dataset and
keeps the washer and dryer kWh side by side. For example, WD90 has label/PDP
washer-side 103 and combo EPA washer 103, while the dryer-component value is
608; the two EPA dryer paths also show 608 for this pattern. WD53 has label
washer-side 103 and combo-EPA dryer-side 319; the ordinary Dryer EPA row has no
annual-kWh value for that pattern. These are component-specific source
observations, not findings. Laundry Center WH46 labels report 94/95 while the
ordinary Dryer EPA candidates show separate dryer rows; they do not link to the
all-in-one combo dataset. The summary now separates SKU-compatible label model
patterns from other model-like PDF tokens and displays EPA fuel type, so e.g.
document-number-like text is not mistaken for a matching model pattern.

The EPA source-row identity check completed in candidate-join run
`35720397828`. `WH46DBH100EWA3` fits EPA model pattern `WH46DBH1**E*` (Electric,
PD ID `2788490`, Current row `row-4w22_yqwp~ghak`); `WH46DBH100GWA3` fits
`WH46DBH1**G*` (Gas, PD ID `2788449`, Current row `row-jgca~eq5m.9d2h`). Both
distinct EPA records report 687 kWh/year and CEF 3.48. This verifies that the
equal values come from two separate source rows, rather than a duplicated join
row. They remain source observations; no value has been altered and no
assessment has been made. The associated label candidates (94/95 kWh/year) are
washer-side Laundry Center values and must not be compared to dryer-side EPA
values.

The same run exposes the WH46 500 records separately: `WH46DBH500EVA3` fits
Electric PD ID `2788488`, row `row-ypmp-fu3m~cfdf` (608 kWh/year, CEF 3.93),
while `WH46DBH500GVA3` fits Gas PD ID `2788448`, row `row-cdmn.hcfe.icef`
(687 kWh/year, CEF 3.48). Their Support/PDP washer-side value discrepancy is
already documented in the Washer source contract; it is not a dryer-side
comparison.

The original Dryer projection filtered Bridge `Support.supports` to entries
named exactly `Energy Guide` before writing the collection artifact. Therefore
the observed 11/54 count describes only canonical-name entries; the other 43
were discarded by our projection and cannot be called empty in Samsung's raw
response. This is a collection-contract blind spot, not evidence that PDP Bridge
lacks their document links. Dryer collection now has an explicit option to
preserve every Support `name`/`type`/`url` triple, and the candidate report will
show all observed Support document names. A fresh hosted collection is required
to determine whether alternate labels or PDF URLs explain the 43. No conclusion
about label absence or compliance is valid before that recapture. The standalone
DV53BB8900HDA2 PDF still has a distinct OCR candidate-extraction gap.

### Full PDP Bridge Support inventory correction (2026-09-22)

The source projection previously persisted only Support entries whose name
matched exactly `Energy Guide`. Therefore the claim that the other 43/54
products had empty Support arrays was false: the original data had already been
filtered before persistence. A fresh complete collection passed in hosted run
`35723240890` (54/54 exact PDPs). Its Support inventory has `User Manual` and
`Warranty` on 54 SKUs each, canonical `Energy Guide` on 11, `Quick Guide` on 2,
and `User manual for all` on 9. Counts overlap by SKU. This confirms the Support
arrays were not empty but does not by itself show that alternate-name entries
are EnergyGuide documents. Workflow
`g3-dryer-support-url-inventory.yml` now checks the already captured URL hosts
and paths for EnergyGuide-like terms without reopening product pages or
fetching documents. Until that result is reviewed, only the 11 canonical-name
links are known to be EnergyGuide URLs.
