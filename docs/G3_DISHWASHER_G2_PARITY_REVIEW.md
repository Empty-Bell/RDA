# G3 dishwasher / G2 refrigerator parity review

Reviewed at commit `5f5d82f`. This is a control-parity review, not a new
compliance decision.

| Control capability | G2 refrigerator | G3 dishwasher | Required follow-up |
|---|---|---|---|
| Current EPA identity candidates | Exact literals, approved terminal-`AA` normalization, and reviewed current-index patterns | Exact normalized literal only | Add the same bounded `*` / `?` current-index pattern projection; retain exact SKU as the finding grain. |
| Energy Star three-point rule | Complete-source and provenance checks before PASS/LOW/HIGH/NO_FINDING | Rule is present, but source completeness/provenance is less explicit | Add replayable coverage and source-run checks before the assessment consumes inputs. |
| EnergyGuide annual value | Reviewed selection/replay precedes numeric assessment | A conservative raw-candidate selection is implemented | Bind selection to a reviewed US EnergyGuide region before findings are enabled. |
| EnergyGuide model identity | Explicitly reviewed two-pattern groups only; terminal-`AA` normalization; report adapter | Raw candidate inclusion is implemented and hosted run passed; mixed US/Canadian pages and OCR candidates are not yet review-bounded, and the report does not consume it | Add a bounded review/selection artifact, then attach its result to the canonical report and dashboard. |
| Annual-energy finding | Missing PDP annual energy -> LOW | Comparison only; no finding | Apply the approved LOW rule after the reviewed EnergyGuide value contract exists. |
| Capacity finding | Numeric PDP/EnergyGuide cubic-foot difference -> MEDIUM, zero tolerance | EnergyGuide capacity is class text such as `Standard`; PDP/EPA use place settings | Excluded by product policy. Do not create a dishwasher capacity comparison or finding. |
| EPA numeric role | EPA is corroboration, not a substitute for EnergyGuide | Same intent, but its selection is not source-run-bound | Preserve corroboration-only behavior while binding it to the same source package. |
| Canonical report | Includes Energy Star, numeric, model-pattern sections and an exact-SKU control summary | Contains Energy Star and numeric observations only | Add model-pattern section, numeric assessment section, and a per-SKU control summary. |
| Dashboard | Renders all control outcomes/findings | Renders Energy Star and numeric observations only | Include model-pattern outcome and later enabled numeric findings. |
| Same-run artifact integrity | Adapters reject different execution-run IDs and coverage drift | Latest successful artifacts may be combined across runs | Add source run IDs and package hashes to every downstream control; reject cross-run joins. |
| Regression and acceptance | Focused unit tests plus hosted acceptance contract | Tests currently cover collection and EnergyGuide retrieval only | Add tests for matching, assessments, report/dashboard adapters, then a short hosted acceptance workflow. |

## Sequencing

1. **Identity parity:** add current EPA wildcard projection and its tests. This
   restores the user-approved interpretation that a current model pattern such
   as `RF23D*9600**` includes its matching exact SKU.
2. **EnergyGuide evidence parity:** create one reviewed-US-region selection
   artifact for annual values and model patterns. It must preserve raw source
   evidence and must not treat Canadian `EnerGuide` text on a mixed page as US
   EnergyGuide evidence.
3. **Assessment and reporting parity:** enable only approved rules, attach the
   model and numeric sections to one same-run canonical report, project the
   exact-SKU control summary, and update the dashboard.
4. **Reliability parity:** add unit and hosted acceptance checks for source-run
   linkage, complete coverage, output counts, and dashboard data coverage.

The following are deliberately *not* parity gaps: historical EPA disqualified
lists (removed by policy), a presumed shared logo between representative and
child SKUs, and a numeric EnergyGuide capacity comparison when the label only
contains a capacity class.
