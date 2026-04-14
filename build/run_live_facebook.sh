#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export PLAYWRIGHT_BROWSERS_PATH="${PROJECT_ROOT}/.playwright-browsers"

VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "[ERROR] Virtual environment not found."
  echo "Please run build/build.sh first."
  exit 1
fi

GAME_NAME="${1:-Whiteout Survival}"
STORAGE="${2:-postgres}"

echo "Running Facebook Ads Library live scraper..."
echo "Game name: ${GAME_NAME}"
echo "Storage: ${STORAGE}"

if [[ "${STORAGE}" == "postgres" ]]; then
  echo "Checking postgres connection and ensuring target database exists..."
  "${VENV_PYTHON}" init_postgres.py
fi

"${VENV_PYTHON}" main.py --platform facebook --scraper-mode live --storage "${STORAGE}" --game-name "${GAME_NAME}"
