# Dashboard Run #19 integration record — 2026-09-28

The mixed-family dashboard reconciles **557 exact models in 11 families** to
11 hosted, source-bound family control artifacts. The local integration gate
returned `execution_status=PASS`, `snapshot_readiness=READY_FOR_FORMAL_REVIEW`,
zero integrity errors, and zero pending family gates. Its four mutually
exclusive model grades are **479 PASS / 29 HIGH / 11 MEDIUM / 38 LOW**.

The six EPA-focused families were reassessed from their frozen source bundles
in [run 36417820738](https://github.com/Empty-Bell/RDA/actions/runs/36417820738)
after applying the approved rule that a missing Specs certification field is
`NOT_APPLICABLE`, while an explicit `No` remains assessable. Their respective
PASS/LOW counts are Range 54/4, Cooktop 20/0, Dryer 54/0, Hood 16/0, Monitor
63/13, and Computer 19/5. The saved-source replay reported no unknown grades.

The [Tablet final assessment](https://github.com/Empty-Bell/RDA/actions/runs/36418451410)
accepted the rendered US PLP's 11 exact SKUs: **11 PASS**, zero findings and
zero readiness gaps. EPA Current identity requires an exact explicit model
token. The PLP population replaced `SM-X930NZSAXAR` with `SM-X930NZAAXAR`;
the dashboard follows that source population and preserves the change in its
run comparison.

Refrigerator, Dishwasher, Washer, and TV retain their separately accepted
hosted artifacts, with exact run IDs recorded in
[integration-manifest.json](integration-manifest.json). The integration gate
also reconciles every model grade and finding code against those artifacts,
every evidence file, the model CSV, all-fields CSV and Excel export.

**G3 overall remains BLOCKED:** the source collections were executed at
different times and do not constitute one unified 11-family source run.
`single_source_run=false` and `overall_product_compliance=NOT_EVALUATED` are
preserved in the integration report. This is a complete, reviewable integrated
dashboard snapshot, not an assertion of whole-product legal compliance.
