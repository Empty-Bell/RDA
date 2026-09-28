# Unified audit operations and publication

The `Unified 11-family full audit` workflow is the only path that refreshes the
public dashboard. Its 11 collection/assessment jobs feed a single source gate.
The build job creates a new dashboard from those same-run artifacts and checks
all 557 current model keys against the accepted assessments. It then verifies
the publication manifest's run ID, source Git SHA, model count and SHA-256 hashes.
Desktop/mobile browser checks run on that exact site directory before upload.
Only a successful build can persist the snapshot and deploy it to Pages.

## Failure behavior

- Any collection, OCR, EPA, assessment or artifact failure makes a family job
  or the source gate fail. The build and deploy jobs are skipped; the last
  validated Pages deployment remains available.
- A changed `main` head between source capture and persistence blocks the
  commit and deployment. No late run can overwrite a newer snapshot.
- The built site and all 11 raw family artifacts are retained in Actions for
  90 days. `docs/` keeps the compact current evidence and cumulative finding
  history in Git. Once raw artifacts expire, the compact evidence and run
  identity remain, but raw source replay for that run is unavailable.
- `publication-manifest.json` and the validated-site artifact identify the
  exact deployed source run. To recover from a bad deployment, dispatch
  `Verify or restore a validated Pages bundle` with the prior successful
  unified source run ID and attempt. Run it first with `deploy=false` to
  check the artifact digest, source Git SHA and per-file hashes; then set
  `deploy=true` to restore that exact bundle. Do not rerun collection or
  silently label an older run as current.

## Schedule

The workflow runs weekly Monday 09:13 KST (Monday 00:13 UTC) using the same
source, dashboard and public Pages gates as manual dispatch. It was activated
after three consecutive distinct complete successful runs following the
failed Range source run: 36461106905, 36465858969 and 36470031260. A failed
scheduled collection still blocks publication and leaves the last validated
dashboard available. The minute avoids GitHub's top-of-hour schedule
congestion.

## Known historical correction

Run #20 originally reused an evidence filename for ten SKUs that appear in
both Washer and Dryer. The source run was replayed into distinct product-family
evidence files without changing its 557 model grades or finding counts. The
publication manifest now rejects reused evidence paths and mismatched
family/model identities. Previously published unqualified URLs may still exist
as historical files; current model links point to qualified evidence.

## Measured baseline and limits

The accepted Run 36438033553 used about 133 MB across 12 artifacts. Its
slowest family jobs (TV and Refrigerator) took about 30 and 29 minutes.
Family jobs have a 120-minute cap, and the validated site directory has a
1 GiB build cap. A cap breach fails the workflow and cannot publish.

Ruleset fingerprints normalize CRLF/LF line endings before hashing Python
source. A platform-only checkout difference must not reset independent
finding confirmation; the Run #21 history replay and source-digest checks are
recorded in `G5_ACCEPTANCE_RECORD.md`.

Publication bundle V2 also normalizes text line endings before hashing so a
Windows Git checkout and the deployed Linux artifact verify to the same
canonical content. XLSX remains byte-hashed. Legacy V1 bundles remain
verifiable from their exact hosted artifacts for rollback.
