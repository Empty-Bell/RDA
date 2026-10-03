# Computer routing investigation — 2026-10-01

## Finding

External root cause is NOT established. Downgrading a finding does not repair
collection. The earlier attribution to a Samsung structural defect was premature.
A static structure is only one possible cause: inventory, backend response,
client hydration and browser state can change without the URL changing.

## Historical evidence (times KST)

| Source run | Capture | KA1US | KG2US |
|---|---|---|---|
| [36709610552](https://github.com/Empty-Bell/RDA/actions/runs/36709610552) | Sep 30 20:39–20:43 | exact verified; stock Y | exact verified; stock Y |
| [36795898093](https://github.com/Empty-Bell/RDA/actions/runs/36795898093), artifact attempt 1 | Oct 1 09:26–09:32 | selected-model mismatch in 3 attempts; stock N | exact verified; stock Y |
| [36824247885](https://github.com/Empty-Bell/RDA/actions/runs/36824247885) | Oct 1 15:23–15:29 | 3 observations routed to NP960UJH-XG2US; stock N | 3 observations routed to NP960UJH-XG2US; stock Y |

Exact SKUs: NP740VJG-KA1US / NP740VJG-KG2US.
First two runs used identical g3_computer_collect.py, browser_runtime.py and
source_contract.py, and Chromium 153.0.8010.12. Exact requested URLs were unchanged.
Both targets retained their shard position and preceding SKUs across all three runs.
Thus a collector code/browser-version/order change does not explain that first transition.
Stock change correlates with KA1US failure but cannot alone explain KG2US.
Historical success proves these are not permanently unusable URL structures.
The old failure artifact lacks selected controls/final URL, preventing a retroactive
claim about precisely which model was selected during the first failure.

Read-only downloaded sources (ignored runtime directory):
- runtime/computer-root-cause/11094430294: successful computer artifact.
- runtime/computer-root-cause/11134495076: scheduled attempt 1 computer artifact.
- runtime/inspect-computer-36824247885/source: latest successful workflow's source.

## Confirmed collector weaknesses and local changes

1. One context shared across a shard allowed cookies/storage to carry between SKUs.
   Now each SKU and retry creates/closes an independent context. Browser version,
   locale and viewport remain unchanged. Isolation removes this confounder; it does
   not prove it caused historical failures.
2. A fixed ten-second delay and single snapshot could sample a transient default.
   Now observe for up to 30 seconds; require four consecutive identical URL/control/
   Continue observations, no earlier than ten seconds. A wrong default gets the full
   window. Retain exact URL, selected controls, purchase SKU, group and Specs checks.
   Recheck selection and URL after Specs and snapshot collection.
3. Failure evidence was incomplete; now save navigation statuses, selected-state
   timeline, ecom response bodies/hashes, observed group IDs, failure DOM and image.
   Preserve original failed files before promoting a successful retry.
4. 'Not selectable' was inferred without attempting selection. Internal failure
   classification now says selected SKU differs from requested. Existing downstream
   routing status remains compatible, but explicitly records root_cause=UNDETERMINED.
   Repeated routing requires HTTP 200 and stable identity of the alternate model in
   every attempt. Missing/unstable controls remain source failures, never PASS.

These are collection safeguards; no loosening of model matching, no exclusion of
PLP option SKUs and no inference of target PDP claims from a representative model.

## Remaining causal verification

Hosted verification is still required; local unit results are not a hosted gate PASS.
Use these two exact SKU links and a working same-family control on the same commit:
- Compare isolated direct navigation against navigation from the rendered PLP option.
- Repeat each route with a new context and retain all observation timelines.
- Compare requested SKU availability in saved ecom bodies with PLP stock values.
- If exact selection emerges only later, timing is implicated; adjust readiness to
  the observed response/state transition rather than increasing blind retries.
- If only warm sessions differ, isolate the responsible cookie/storage behavior.
- If isolated runs and real PLP navigation consistently substitute another SKU while
  backend availability changes, provide that trace to the site owner.
- If unstable behavior remains, retain source uncertainty; don't declare the issue
  resolved or a regulatory violation on the basis of a single outcome.

Public HIGH-to-MEDIUM change in local commit 6e7bd96 and these safeguards are not
published. A prior push was rejected by automatic approval review due the earlier
read-only heartbeat restriction. No push or workflow dispatch was retried in this
investigation.


## Live tests completed after user requested verification

Environment: local Windows, Playwright 1.63.0, Chromium 153.0.8010.12.
These are actual public-page observations; not a GitHub-hosted gate result.
Each direct attempt starts a new browser context. Round 2 reverses product order.

| Exact SKU | Direct attempts | Result |
|---|---:|---|
| NP740VJG-KA1US | 3 | All select NP960UJH-XG2US instead |
| NP740VJG-KG2US | 3 | All select NP960UJH-XG2US instead |
| NP760VJG-KG2US, control | 3 | All VERIFIED_EXACT_IDENTITY, including exact Specs |

The alternate model remained selected throughout the 30-second observation
window on all six failed direct attempts. Shared per-shard storage and the old
10-second snapshot are therefore not necessary for the current failure to occur.
This does not exclude their impact on older runs.

Two independent PLP-route trials selected the visible 512 GB option. The card
became Galaxy Book6 14-inch / NP740VJG-KA1US, with Notify me instead of Buy.
Following its actual displayed review link again selected NP960UJH-XG2US in both
trials. No equivalent KG2US-specific clickable option was established; do not
claim a PLP-route test for KG2US.

Both fresh browser-captured PF responses now mark KA1US and KG2US stockFlag=N.
The ecom responses captured on all nine direct visits also mark both inventory
status=N, max_quantity_allowed=0; the normal control is Y with positive quantity.
The earlier artifact's KG2US stockFlag=Y is not its current state.

Separate synthetic tests intercepted only the target SKU's ecom inventory in an
isolated browser (N->Y and quantity 0->1). Both models STILL selected the alternate
model. These are not actual stock observations or compliance evidence. They show
that changing those two response fields alone does not restore exact selection;
other configuration/availability inputs or routing decisions may be involved.
No server data or purchases were changed.

The initial PLP automation attempts were blocked by the cookie notice. After
using its actual Continue button, the two completed route trials above succeeded.
A bare HTTP PF request returned 403; fresh PF evidence was instead captured from
the browser's normal successful PLP response. These failed probes are retained.

Raw local evidence: runtime/computer-live-test/ (summary.json, results.json,
round-1 through round-3, plp-route-6/7.json, current-pf-6/7.json,
synthetic-stock-*.json and the reproduction scripts). The runtime directory is
ignored by Git. Synthetic evidence remains separate from real source captures.

Code checks: 11 relevant unit/pipeline tests PASS and git diff --check PASS.
During review, corrected recovery to copy all evidence files (including new ecom
fixtures) and limited navigation diagnostics to main-frame document responses.
No public dashboard update, push or hosted workflow execution occurred.

Conclusion: the two failures are reproducible NOW through direct navigation and,
for KA1US, actual PLP navigation. Current evidence supports a real configurator
selection problem in the tested environment rather than a one-off parser false
positive. The exact historical transition and frontend decision causing fallback
remain unproven. Keep PLP SKUs in scope, keep target PDP claims unverified, and do
not claim a stock-based automatic fix or convert this into a certification HIGH.
