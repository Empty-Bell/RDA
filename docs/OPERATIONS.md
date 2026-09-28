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
  exact deployed source run. To recover from a bad deployment, retrieve the
  latest previously validated-site artifact, verify its manifest and hashes,
  then deploy that artifact through a controlled Pages workflow. Do not rerun
  collection or silently label an older run as current.

## Schedule activation

Keep this workflow manually dispatched until three consecutive complete
source runs with different run IDs pass the source, dashboard and public Pages
checks. A failed run resets the streak. Once that condition is met, enable a
weekly schedule; each scheduled run uses the same gates and publication path.

## Known historical correction

Run #20 originally reused an evidence filename for ten SKUs that appear in
both Washer and Dryer. The source run was replayed into distinct product-family
evidence files without changing its 557 model grades or finding counts. The
publication manifest now rejects reused evidence paths and mismatched
family/model identities. Previously published unqualified URLs may still exist
as historical files; current model links point to qualified evidence.
