# Hosted runner contract

Baseline: ubuntu-24.04 x64, Python 3.12.14, headless Chromium, CPU RapidOCR, PyMuPDF primary.
No persistent state, local profile, private network, GPU, Windows OCR or prewarmed cache required.
Probe installs explicitly with hashed runtime/build-tool locks, no build isolation or
saved pip cache, plus pip check and a pinned ONNX/configuration integrity gate before
source collection. Runtime freeze/controlled recovery passed two cold jobs in run
35166865310 with full source/EPA regression; see RUNTIME_FREEZE_CONTRACT.md and
runtime-freeze-recon.json. Application dependencies/model resources/Actions SHAs
are pinned; the hosted image/system apt libraries remain GitHub-managed inputs.

Bootstrap/probe job timeout: 20 minutes. Initial HTTP concurrency is sequential.
Free disk gate: 3 GiB. OCR worker 1, ONNX/OpenCV threads 1/1, render 2x.
Probe fixtures are synthetic or sanitized captures; no compliance verdict.
Full phase PASS requires actual Actions URL, SHA, attempt, logs and artifact manifest.

Browser identity uses scripts/browser_runtime.py: actual installed Linux Chromium UA
with HeadlessChrome replaced by Chrome, preserving OS/browser version; en-US,
desktop 1365x768, no mobile/touch profile. Record native/effective UA and browser version.
Use the same context for browser and context.request calls. pf_search request UA
is verified against the configured identity. A UA change does not prove 403 is solved;
bounded retries and pipeline-health classification remain required.
