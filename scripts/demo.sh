#!/usr/bin/env bash
# One-command demo: legal clause -> norm -> control -> evaluation.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m src.demo
