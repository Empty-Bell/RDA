# Unified source and bounded control acceptance — Run #20

## Decision and scope

**PASS for G3 and G4 bounded collection and approved control execution.**
[GitHub Actions run 36438033553](https://github.com/Empty-Bell/RDA/actions/runs/36438033553)
at commit `c533b1f` freshly collected and assessed all 11 families in one
execution. All 11 family jobs and the final unified gate passed. The gate
reported `single_source_run=true`, 557 exact SKUs, zero integrity errors and
485 PASS / 23 HIGH / 11 MEDIUM / 38 LOW. No SKU was left unclassified.

The G3 families (Dishwasher, Washer, TV) cover 223 SKUs: 205 PASS, 9 HIGH,
4 MEDIUM and 5 LOW. The seven G4 EPA-focused families cover 259 SKUs:
237 PASS and 22 LOW. The accepted G2 refrigerator covers the remaining 75:
43 PASS, 14 HIGH, 7 MEDIUM and 11 LOW. These grades evaluate the implemented
disclosure controls; **whole-product legal compliance remains NOT_EVALUATED**.

The Run #20 Pages source was built from this run's artifact set only. Its local
integration gate returned `execution_status=PASS`,
`formal_readiness=READY_FOR_FORMAL_REVIEW`, `single_source_run=true`, zero
pending family gates and zero integrity errors. The gate reconciled each model
grade and finding against the accepted family assessment, evidence files and
CSV/Excel exports. [The integration manifest](integration-manifest.json) binds
all 11 dashboard inputs to run `36438033553`.

## Change from Run #19

The exact model population remains 557. Six TV models changed from HIGH to
PASS after current EnergyGuide evidence became available:

| Model | Previous issue | Current evidence |
| --- | --- | --- |
| `QN55LS03HEFXZA` | Label unreadable | Printed model `QN55LS03HEF` matches |
| `QN65LS03HEFXZA` | Label unreadable | Printed model matches |
| `QN75LS03HEFXZA` | Label unreadable | Printed model matches |
| `QN85LS03HEFXZA` | Label unreadable | Printed model matches |
| `QN98LS03HEFXZA` | Label unreadable | Printed model matches |
| `UN43U8000HFXZA` | Label document missing | Accessible label prints `UN43U8000HF` |

The approved fixed-prefix matching rule connects those printed label models
to the exact PDP SKUs. TV now has 163 PASS and two HIGH. The remaining TV HIGH
models are `QN77S84FAEXZA` (ENERGY STAR eligibility candidate) and
`UN50U8000HFXZA` (EnergyGuide document missing candidate). All other family
grades are unchanged from Run #19. The dashboard's previous-run comparison
lists exactly these six resolutions.

## Source handling and limits

In a preceding attempt, Samsung's listed `QN85LS03FWFXZA` PDP URL temporarily
landed on the 75-inch SKU, so the audit failed rather than accepting the wrong
model. The TV collector now retries failed exact-SKU identity captures within
the same run and retains prior attempts. In accepted run `36438033553`, all
165 TV PDPs verified exact identity without invoking a retry. The TV label
comparison had zero readiness gaps.

The [hosted dashboard integration gate](https://github.com/Empty-Bell/RDA/actions/runs/36443526583)
also passed with `single_source_run=true`, no pending family gates and no
integrity errors. The [Pages deployment](https://github.com/Empty-Bell/RDA/actions/runs/36443523560)
passed; the [live dashboard](https://empty-bell.github.io/RDA/) served Run #20
with 557 models, and its JSON, both CSV exports, Excel file and a model
evidence URL returned HTTP 200. **G7 publication is accepted for Run #20.**

This record does not close G5 history or G6 operational hardening/scheduling.
It does not turn control PASS into an overall product compliance verdict.
