#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "[ERROR] Virtual environment not found."
  echo "Please run build/build.sh first."
  exit 1
fi

LIMIT="${1:-20}"

echo "Viewing latest ${LIMIT} records from Postgres..."
"${VENV_PYTHON}" view_data.py --limit "${LIMIT}"
