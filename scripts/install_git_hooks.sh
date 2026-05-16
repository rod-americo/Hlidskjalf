#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Este diretorio ainda nao e um repositorio git." >&2
  echo "Rode 'git init' antes de instalar os hooks." >&2
  exit 1
fi

git config core.hooksPath .githooks
echo "Git hooks instalados em .githooks"
