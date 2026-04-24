#!/usr/bin/env bash
# check.sh — preflight verification for share_learn_research.
# Reports what's installed and what's missing. Non-zero exit if anything
# required for /crawl is absent.
# Called by `make check`. Also safe to invoke directly.

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ok()   { printf '\033[1;32m ✓\033[0m %-40s %s\n' "$1" "${2:-}"; }
miss() { printf '\033[1;31m ✗\033[0m %-40s %s\n' "$1" "${2:-MISSING}" >&2; }
warn() { printf '\033[1;33m !\033[0m %-40s %s\n' "$1" "${2:-}"; }

missing=0
note() { [[ "${1:-}" == "required" ]] && missing=$((missing+1)); }

check_venv() {
  local name="$1"
  local req="${2:-required}"   # required | optional
  local dir=".venv-$name"
  if [[ -x "$dir/bin/python" ]]; then
    local ver
    ver=$("$dir/bin/python" --version 2>&1 | awk '{print $2}')
    ok "$dir" "python $ver"
  else
    if [[ "$req" == "required" ]]; then
      miss "$dir"; note required
    else
      warn "$dir" "(optional — not installed)"
    fi
  fi
}

check_file() {
  local path="$1"
  local req="${2:-required}"
  if [[ -e "$path" ]]; then
    ok "$path"
  else
    if [[ "$req" == "required" ]]; then
      miss "$path"; note required
    else
      warn "$path" "(optional)"
    fi
  fi
}

echo "== Python venvs =========================================="
check_venv scrapling required     # the Tier-A + Tier-B backbone
check_venv scrapy    required     # recurrent pipelines framework
check_venv crawl4ai  optional     # comparison tool
check_venv r3        optional     # R3 comparison round tools

echo
echo "== Node dependencies ====================================="
check_file node_modules/@playwright/mcp    required
check_file node_modules/chrome-devtools-mcp required

echo
echo "== Claude Code assets ===================================="
check_file .claude/skills/crawl-thesis/SKILL.md required
check_file .claude/skills/web-scraper/SKILL.md  required
check_file .claude/agents/crawl-specialist.md   required
check_file .claude/commands/crawl.md            required

echo
echo "== Optional proxy pool ==================================="
if [[ -f .proxies ]]; then
  proxies_count=$(wc -l < .proxies | awk '{print $1}')
  ok ".proxies" "$proxies_count proxy URL(s)"
else
  warn ".proxies" "(none — R9 proxy flip test not runnable)"
fi

echo
if [[ $missing -gt 0 ]]; then
  printf '\033[1;31m%d required component(s) missing.\033[0m Run: \033[1mmake venvs\033[0m\n' "$missing" >&2
  exit 1
fi
printf '\033[1;32mAll required components present.\033[0m Run: \033[1mclaude\033[0m and try \033[1m/crawl <URL>\033[0m\n'
