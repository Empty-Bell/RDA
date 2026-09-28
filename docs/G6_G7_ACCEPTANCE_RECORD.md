# G6 operations and G7 Pages acceptance — 2026-09-29

## Gate result

**G6 PASS; G7 PASS** for the approved bounded 11-family audit controls.
Three consecutive successful, distinct full source runs after the failed
Range source run passed every collection, integration, publication and public
browser gate: [36461106905](https://github.com/Empty-Bell/RDA/actions/runs/36461106905),
[36465858969](https://github.com/Empty-Bell/RDA/actions/runs/36465858969) and
[36470031260](https://github.com/Empty-Bell/RDA/actions/runs/36470031260).
The weekly Monday 00:13 UTC / 09:13 KST schedule is enabled in the same
gated workflow.
The earlier [36458735360](https://github.com/Empty-Bell/RDA/actions/runs/36458735360)
failed closed on a transient wrong-model Range PDP redirect, so it is not in
the streak and did not replace the public dashboard.

## Hosted evidence already complete

- Run 36461106905 passed all 11 fresh family jobs, the one-run 557-model
  source gate, publication bundle build, desktop/mobile browser checks, Git
  persistence, Pages deployment, and public browser checks.
- The published Run #22 contains 485 PASS, 23 HIGH, 11 MEDIUM and 38 LOW.
  Its 557 exact-model grade and finding-code pairs match Run #21 exactly;
  there were no population changes. Its V2 publication bundle verified on
  Windows after the Linux deployment: 566 hashed files, matching run ID and
  source Git SHA.
- Run 36461106905 used 14 artifacts totaling 174.6 MB. Its slowest family
  job was Refrigerator at 30.1 minutes; the 11 jobs are capped at 120 minutes
  each, and the site build is capped at 1 GiB.
- Run 36465858969 independently passed all 11 family jobs and the same
  integration, publication and public checks. Run #23 and Run #22 contain the
  same 557 exact models, grades and finding-code sets; no model changed.
- Run 36470031260 independently passed the same gates. Run #24 and Run #23
  again contain the same 557 exact models, grades and finding-code sets; no
  model changed. Its 566-file V2 bundle passed a separate Windows hash check
  against the Linux-built deployment, and the public Pages manifest identifies
  Run #24 and 557 models.
- [Recovery run 36466169003](https://github.com/Empty-Bell/RDA/actions/runs/36466169003)
  verified and actually redeployed the same validated Run #22 bundle. The
  public manifest and model data still identify Run #22 and 557 models.
- The [hosted integration gate 36458542324](https://github.com/Empty-Bell/RDA/actions/runs/36458542324)
  passed failure-injection contracts for source errors, missing/wrong-run
  artifacts and bundle tampering. A separate
  [verify-only recovery rehearsal 36458590077](https://github.com/Empty-Bell/RDA/actions/runs/36458590077)
  passed for the prior V1 bundle.

## Ongoing operation

The weekly run uses the same exact-SKU and source integrity checks. Any
collection or publication failure blocks that run's deployment while the last
validated dashboard stays live. Review a changed finding against its saved
source before treating it as an actual disclosure change; the history engine
requires a second independent complete observation before marking a missing
finding resolved. Raw Actions artifacts are retained for 90 days. Recovery
uses a previously successful validated-site artifact and verifies its digest,
run identity, source SHA and file hashes before deployment.

This gate concerns the approved bounded regulatory disclosure controls, not
a final whole-product legal compliance determination.
