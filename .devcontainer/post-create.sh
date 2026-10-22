#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip

if [ -f pyproject.toml ]; then
  # Once Phase 1 has created pyproject.toml, it is the single source of dependencies.
  pip install -e ".[dev]"
else
  # Bootstrap before pyproject.toml exists (start of Phase 1).
  pip install flet pytest ruff
fi

# Auto-activate the venv in every new terminal.
grep -q '.venv/bin/activate' ~/.bashrc || \
  echo "source $PWD/.venv/bin/activate" >> ~/.bashrc

echo "Done. Run 'claude' to start Claude Code (first run asks you to log in)."
