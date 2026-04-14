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

PLATFORM="${1:-tiktok}"
SCRAPER_MODE="${2:-live}"
GAME_NAME="${3:-Whiteout Survival}"

echo "Running scraper with Postgres storage..."
echo "Platform: ${PLATFORM}"
echo "Scraper mode: ${SCRAPER_MODE}"
echo "Game name: ${GAME_NAME}"

echo "Checking postgres connection and ensuring target database exists..."
"${VENV_PYTHON}" init_postgres.py

"${VENV_PYTHON}" main.py --platform "${PLATFORM}" --scraper-mode "${SCRAPER_MODE}" --storage postgres --game-name "${GAME_NAME}"
