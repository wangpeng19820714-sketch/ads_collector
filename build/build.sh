#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

unset PIP_NO_INDEX HTTP_PROXY HTTPS_PROXY ALL_PROXY GIT_HTTP_PROXY GIT_HTTPS_PROXY

echo "[1/7] Project root: ${PROJECT_ROOT}"

PYTHON_BOOTSTRAP=""

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BOOTSTRAP="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BOOTSTRAP="python"
fi

if [[ -z "${PYTHON_BOOTSTRAP}" ]]; then
  echo "[ERROR] No usable Python runtime was found."
  echo "Install Python 3.10+ and rerun this script."
  exit 1
fi

echo "Using Python bootstrap: ${PYTHON_BOOTSTRAP}"

echo "[2/7] Creating virtual environment..."
if [[ ! -x ".venv/bin/python" ]]; then
  "${PYTHON_BOOTSTRAP}" -m venv .venv
else
  echo "Virtual environment already exists. Reusing it."
fi

VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

echo "[3/7] Checking pip..."
if ! "${VENV_PYTHON}" -m pip --version >/dev/null 2>&1; then
  echo "Virtual environment pip is missing. Bootstrapping pip..."
  "${VENV_PYTHON}" -m ensurepip --upgrade
fi
"${VENV_PYTHON}" -m pip --version

echo "[4/7] Installing Python dependencies..."
"${VENV_PYTHON}" -m pip install -r requirements.txt

echo "[5/7] Installing Playwright browser..."
export PLAYWRIGHT_BROWSERS_PATH="${PROJECT_ROOT}/.playwright-browsers"
mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}"
"${VENV_PYTHON}" -m playwright install chromium

echo "[6/7] Creating runtime directories..."
mkdir -p logs
mkdir -p build/output

echo "[7/7] Running smoke tests..."
"${VENV_PYTHON}" -m pytest -q

cat <<'EOF'

[SUCCESS] Deployment bootstrap completed.

Activate venv:
    source .venv/bin/activate

Run mock mode:
    python main.py --platform tiktok --scraper-mode mock --storage memory

Run TikTok live mode:
    python main.py --platform tiktok --scraper-mode live --storage memory --game-name "Whiteout Survival"

Run Facebook live mode:
    python main.py --platform facebook --scraper-mode live --storage memory --game-name "Whiteout Survival"

Run viewer:
    python dashboard.py
EOF
