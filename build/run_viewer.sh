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

export ADS_VIEWER_HOST="${ADS_VIEWER_HOST:-127.0.0.1}"
export ADS_VIEWER_PORT="${ADS_VIEWER_PORT:-8787}"

echo "Starting Ads Viewer at http://${ADS_VIEWER_HOST}:${ADS_VIEWER_PORT} ..."
"${VENV_PYTHON}" dashboard.py
