#!/usr/bin/env bash
set -euo pipefail
mkdir -p runtime
phase0_bootstrap_stage=begin
trap 'phase0_exit_code=$?; python scripts/bootstrap_record.py "$phase0_bootstrap_stage" "$phase0_exit_code"; exit "$phase0_exit_code"' ERR
python scripts/bootstrap_record.py begin 0
phase0_bootstrap_stage=locked_build_tools
python -m pip install --index-url https://pypi.org/simple --no-cache-dir --require-hashes --no-deps -r requirements-tools.lock
python scripts/bootstrap_record.py "$phase0_bootstrap_stage" 0
phase0_bootstrap_stage=locked_runtime_packages
python -m pip install --index-url https://pypi.org/simple --no-cache-dir --require-hashes --no-deps --no-build-isolation -r requirements-probe.lock
python scripts/bootstrap_record.py "$phase0_bootstrap_stage" 0
phase0_bootstrap_stage=dependency_health
python -m pip check
python -m pip freeze --all > runtime/dependencies.txt
python scripts/bootstrap_record.py "$phase0_bootstrap_stage" 0
phase0_bootstrap_stage=model_integrity
python scripts/runtime_integrity.py prepare
python scripts/bootstrap_record.py "$phase0_bootstrap_stage" 0
phase0_bootstrap_stage=browser_install
python -m playwright install --with-deps chromium
python scripts/bootstrap_record.py "$phase0_bootstrap_stage" 0
python scripts/bootstrap_record.py complete 0
