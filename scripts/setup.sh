#!/usr/bin/env bash
set -euo pipefail

# Repository bootstrap script for developers and CI.
# Creates a local virtual environment and installs runtime + tooling deps.

PYTHON_VERSION=${PYTHON_VERSION:-3.11.9}
VENV_DIR=${VENV_DIR:-.venv}
ALLOW_OFFLINE_FALLBACK=${ALLOW_OFFLINE_FALLBACK:-1}

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

# Warn if python version mismatch
CURRENT_PYTHON=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
if [[ ${CURRENT_PYTHON} != ${PYTHON_VERSION}* ]]; then
  echo "[setup] Expected python ${PYTHON_VERSION}, found ${CURRENT_PYTHON}." >&2
fi

create_venv() {
  local extra=("$@")
  python3 -m venv "${VENV_DIR}" "${extra[@]}"
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
  python -m ensurepip --upgrade >/dev/null
}

cleanup() {
  deactivate >/dev/null 2>&1 || true
}

create_venv
trap cleanup EXIT

install_requirements() {
  local pip_args=()
  [[ -f requirements.txt ]] && pip_args+=(-r requirements.txt)
  [[ -f requirements-dev.txt ]] && pip_args+=(-r requirements-dev.txt)

  if [[ ${#pip_args[@]} -eq 0 ]]; then
    return 0
  fi

  set +e
  python -m pip install --disable-pip-version-check --no-input "${pip_args[@]}"
  local status=$?
  set -e
  return "${status}"
}

verify_environment() {
  local runtime_imports optional_imports
  runtime_imports=$'fastapi:fastapi\nuvicorn[standard]:uvicorn\npydantic:pydantic\npython-jose[cryptography]:jose\nredis:redis\nhttpx:httpx\nopenai:openai\norjson:orjson\npython-dotenv:dotenv\nrequests:requests'
  optional_imports=$'pytest:pytest\npytest-asyncio:pytest_asyncio\nruff:ruff\nmypy:mypy\nbandit:bandit\npip-audit:pip_audit\npip-licenses:piplicenses'

  REQUIRED_IMPORTS="${runtime_imports}" OPTIONAL_IMPORTS="${optional_imports}" python - <<'PY'
import os
import sys
from importlib import import_module


def inspect(env_key: str, fatal: bool) -> bool:
    blob = os.environ.get(env_key, "")
    entries = [line.strip() for line in blob.splitlines() if line.strip()]
    if not entries:
        return False

    missing = []
    for entry in entries:
        requirement, module = entry.split(":", 1)
        try:
            import_module(module)
        except Exception as exc:  # pragma: no cover - surfaced to user
            missing.append(f"{requirement} (module '{module}'): {exc}")

    if missing:
        header = "Missing required packages" if fatal else "Optional developer tools missing"
        print(f"[setup] {header}:")
        for item in missing:
            print(f"  - {item}")
    return bool(missing) and fatal


failed = inspect("REQUIRED_IMPORTS", True)
if failed:
    sys.exit(1)

inspect("OPTIONAL_IMPORTS", False)
PY
}

USED_FALLBACK=0
if ! install_requirements; then
  if [[ ${ALLOW_OFFLINE_FALLBACK} -ne 1 ]]; then
    echo "[setup] Dependency installation failed. Re-run with network access or set ALLOW_OFFLINE_FALLBACK=1." >&2
    exit 1
  fi

  echo "[setup] pip install failed; attempting offline fallback via system site-packages." >&2
  cleanup
  rm -rf "${VENV_DIR}"
  create_venv --system-site-packages
  USED_FALLBACK=1
fi

verify_environment

if [[ ${USED_FALLBACK} -eq 1 ]]; then
  echo "[setup] Environment ready using system site-packages fallback. Activate via: source ${VENV_DIR}/bin/activate" >&2
  echo "[setup] Optional tools may be unavailable until dependencies can be installed from PyPI." >&2
else
  echo "[setup] Environment ready. Activate via: source ${VENV_DIR}/bin/activate"
fi
