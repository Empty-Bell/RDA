#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-probe.txt
python -m playwright install --with-deps chromium
python -m pip freeze > runtime/dependencies.txt
