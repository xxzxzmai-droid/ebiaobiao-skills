#!/usr/bin/env bash
set -euo pipefail

FORCE=0
TARGETS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGETS+=("$2")
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      echo "Usage: ./install.sh [--target <skills-dir>] [--force]"
      echo "Default targets: ~/.codex/skills and ~/.claude/skills"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${HOME}/.codex/skills" "${HOME}/.claude/skills")
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  for skill in "$ROOT"/skills/ebiaobiao-*; do
    name="$(basename "$skill")"
    dest="$target/$name"
    if [[ -e "$dest" && "$FORCE" != "1" ]]; then
      echo "skip existing: $dest"
      continue
    fi
    rm -rf "$dest"
    cp -R "$skill" "$dest"
    find "$dest" -type d \( -name node_modules -o -name dist -o -name __pycache__ \) -prune -exec rm -rf {} +
    find "$dest" -type f \( -name package-lock.json -o -name "*.pyc" \) -delete
    echo "installed: $dest"
  done
done

echo "done"
