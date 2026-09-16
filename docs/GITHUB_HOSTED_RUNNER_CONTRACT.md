# Hosted runner contract

Baseline: ubuntu-24.04 x64, Python 3.12, headless Chromium, CPU RapidOCR, PyMuPDF primary.
No persistent state, local profile, private network, GPU, Windows OCR or prewarmed cache required.
Probe installs explicitly; direct versions are pinned. Transitive dependency lock remains a follow-up
after the first hosted install; pip freeze is recorded for reproducibility.

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
