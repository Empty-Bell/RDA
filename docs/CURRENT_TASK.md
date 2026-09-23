# Current task continuation — 2026-09-23

## Active work

G0 and G1 remain accepted. G2 refrigerator is still the formal open gate; downstream G3/G4 family audits are preparatory and do not accept G2 or whole-product compliance.

### Approved, reusable audit rule

For the EPA ENERGY STAR publication check, compare current US EPA model registration with three separate Samsung publication points: PLP logo, PDP logo, and PDP Specs certification. Registered plus all three present is PASS; any confirmed missing point for a registered model is LOW; unregistered plus any displayed point is HIGH; unregistered plus all three absent is display PASS/no finding. Incomplete collection, unknown EPA market, or unsupported surface remains NOT_EVALUATED. Legal applicability and overall product compliance stay NOT_EVALUATED.

### Latest completed family — Monitor

Hosted run [35820239750](https://github.com/Empty-Bell/RDA/actions/runs/35820239750) passed on ubuntu-24.04. Both suites passed (12 tests total). Complete collection: 76/76 exact PDP SKUs; the current Samsung EPA Displays dataset returned 146 Samsung rows (54 Monitor, 92 Signage Display). The user explicitly approved omitting exactly one leading `L` from Monitor PDP SKUs for EPA pattern comparison; literal SKU matching remains first, and the rule is Monitor-specific. A complete strict positional match found 13 US EPA Monitor registrations and 63 with no current matching Monitor row. All 76 had PLP logo, PDP logo, and Specs certification observed absent. Final ENERGY STAR publication outcome: 13 LOW, 63 PASS, 0 HIGH, 0 NOT_EVALUATED. The full per-SKU evidence is in [artifact 10733565048](https://github.com/Empty-Bell/RDA/actions/runs/35820239750/artifacts/10733565048). Legal applicability and overall product compliance are NOT_EVALUATED. Monitor’s ENERGY STAR publication-consistency family slice is complete; this does not close G2/G4.

The 13 LOW SKUs: LS27B804PXNXGO, LS27D802UANXGO, LS27H802UANXZA, LS32D708EBNXGO, LS32D800UBNXGO, LS32D804UANXGO, LS32H802UANXZA, LS34C650TANXGO, LS34C650UANXGO, LS34C650VANXGO, LS37D700EANXZA, LS37D800UANXZA, LS40H850TANXZA.

### Next — Computer

Implement the EPA-only per-SKU collection and model/publication comparison for the disjoint Samsung consumer computer population: Galaxy Book and Chromebook source legs. The existing bounded source reconnaissance established 23 Galaxy Book SKUs plus one Chromebook SKU (24 exact SKUs total), with EPA Computers V9.0 dataset `rxdj-2c88`. Preserve the source-leg provenance and exact CPU/RAM/OS configuration; verify PDP identity with selected model controls, visible Continue SKU, and exactly one matching Specs record. Do not collect FTC EnergyGuide or compare battery Wh/adapter W to annual energy. Do not reuse Monitor’s leading-L omission for Computer. Surface genuinely ambiguous model-pattern examples before assigning an EPA absence or HIGH outcome.

Relevant source contract: `docs/COMPUTER_SOURCE_CONTRACT.md`; accepted bounded recon: run [35114575198](https://github.com/Empty-Bell/RDA/actions/runs/35114575198). Existing source artifacts expire 2026-09-30 UTC, so preserve/reuse only after confirming they remain available and the run identity/hash.
Next family after Computer: Tablet using the same EPA Computers dataset, then review the remaining G4 family gates and the cross-family plan before dashboard implementation.

### Token and execution guidance

GitHub Actions use deterministic Python and no LLM calls. For routine adapter/candidate code, test review, and hosted-result inspection, recommended model is GPT-5.6 Luna low. Use Terra medium only if EPA model-pattern interpretation or product applicability requires a real policy decision. The Actions runtime must never call an LLM.
