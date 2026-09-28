# G5 finding history acceptance — 2026-09-29

**Status: PASS** for the user-approved independent source reconfirmation rule.

- The source-bound Run #20 population contains 557 exact models. The six TV
  findings absent from Run #20 remain `OPEN` with a confirmation candidate;
  none was labeled `RESOLVED` on a single changed source observation.
- The hosted dashboard integration run
  [36451760666](https://github.com/Empty-Bell/RDA/actions/runs/36451760666)
  passed the history lifecycle replay and accepted the 11-family snapshot.
- Replay covers `NEW`, `OPEN`, pending confirmation, `RESOLVED` and
  `REOPENED`, plus failed runs, model scope exit/entry, rule fingerprint
  changes, identical-run replay and conflicting replay. First/latest/resolved
  timestamps are asserted in the lifecycle contract.
- Current PASS/HIGH/MEDIUM/LOW grades remain facts of the current validated
  snapshot. The finding lifecycle is separate and does not imply a final legal
  compliance conclusion.

Run #21 [36453890712](https://github.com/Empty-Bell/RDA/actions/runs/36453890712)
passed all 11 source families, the integration gate and public deployment.
Its 557 grades and findings exactly matched Run #20. The six TV candidates
were absent again in this distinct source run and are now `RESOLVED`.

The first history build incorrectly compared CRLF bytes from the Windows
checkout with LF bytes from the Linux runner and treated identical Python
rules as a change. The normalized rule fingerprint is
`93817ce4aa68f9f9d29ebac6d6a01b4b211863cfa2db81f7d0b93deb1b6066b4`.
No assessment/comparison rule files changed between the historical snapshot
commit `c533b1f` and the Run #21 source commit `8597057`; all three saved
snapshot grade/finding digests were verified before replay. The correction
changes only lifecycle history and Run #21 comparison presentation.

Three later distinct complete runs, [#22](https://github.com/Empty-Bell/RDA/actions/runs/36461106905),
[#23](https://github.com/Empty-Bell/RDA/actions/runs/36465858969) and
[#24](https://github.com/Empty-Bell/RDA/actions/runs/36470031260), kept the
same 557 exact models and identical per-model grades/finding codes. The six
independently resolved TV findings remain `RESOLVED`; 82 other finding keys
remain `OPEN` in Run #24 history.
