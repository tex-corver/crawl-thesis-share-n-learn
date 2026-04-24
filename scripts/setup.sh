#!/usr/bin/env bash
# setup.sh — idempotent installer for share_learn_research tool stack.
# Safe to re-run; skips anything already present.
# Each component is independent — a failure in one does not abort the rest.
# Called by `make venvs`. Prefer `make venvs` unless debugging.

set -u  # -e deliberately OFF — we want to continue on per-component failure

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m ✓\033[0m %s\n' "$*"; }
skip() { printf '\033[1;33m ~\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m !\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m ✗\033[0m %s\n' "$*" >&2; }

FAILURES=()
mark_fail() { FAILURES+=("$1"); }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { fail "$1 not installed — required for setup"; exit 1; }
}

log "Checking prerequisites"
require_cmd python3
require_cmd npm
require_cmd curl
ok "python3 $(python3 --version | awk '{print $2}') · npm $(npm -v) · curl present"

# ---- Python venvs ---------------------------------------------------------
#
# Each venv install is wrapped so a failure in one doesn't abort the rest.
# The per-venv body should return 0 on success, non-zero on failure.

install_venv() {
  local name="$1"; shift
  local dir=".venv-$name"
  if [[ -x "$dir/bin/python" ]]; then
    skip "$dir already present"
    return 0
  fi
  log "Creating $dir"
  if ! python3 -m venv "$dir"; then
    fail "$dir — venv creation failed"
    mark_fail "$dir"
    return 1
  fi
  # shellcheck source=/dev/null
  source "$dir/bin/activate"
  pip install --quiet --upgrade pip >/dev/null
  if "$@"; then
    ok "$dir ready"
    deactivate
    return 0
  else
    fail "$dir — install step failed (see errors above)"
    deactivate
    mark_fail "$dir"
    return 1
  fi
}

install_venv scrapy \
  pip install --quiet scrapy scrapy-playwright

# Scrapling — replace `scrapling install` with the non-sudo subset:
#   * pip install downloads the library + camoufox peer dependency
#     (scrapling[fetchers] only pulls curl_cffi + playwright; camoufox is
#     a separate package that Scrapling's StealthyFetcher imports at runtime)
#   * playwright install chromium  — downloads browser binary (no system deps)
#   * camoufox fetch               — downloads the Camoufox Firefox build + GeoIP DB
# We deliberately skip `playwright install-deps chromium` (which needs sudo
# to apt-get browser system libraries). If Chromium/Camoufox later fails to
# launch for missing system libs, the user should run the playwright deps
# command once with sudo — printed in the warning footer.
install_venv scrapling bash -c '
  pip install --quiet "scrapling[fetchers]" "camoufox[geoip]" \
    && python -m playwright install chromium \
    && python -m camoufox fetch
'

install_venv crawl4ai bash -c '
  pip install --quiet crawl4ai \
    && python -m playwright install chromium
'

install_venv r3 \
  pip install --quiet curl_cffi nodriver botasaurus

# ---- Node dependencies ----------------------------------------------------

if [[ -d node_modules/@playwright/mcp ]]; then
  skip "node_modules/@playwright/mcp already present"
else
  log "Running npm install"
  if npm install --silent; then
    ok "node_modules ready"
  else
    fail "npm install failed"
    mark_fail "node_modules"
  fi
fi

# ---- Optional: web-scraper upstream skill ---------------------------------

if [[ ! -f .claude/skills/web-scraper/SKILL.md ]]; then
  log "Cloning yfe404/web-scraper into .claude/skills/web-scraper"
  if git clone --depth 1 https://github.com/yfe404/web-scraper .claude/skills/web-scraper; then
    rm -rf .claude/skills/web-scraper/.git
    ok "web-scraper skill installed"
  else
    warn ".claude/skills/web-scraper — git clone failed (optional, not fatal)"
  fi
else
  skip ".claude/skills/web-scraper already present"
fi

# ---- Summary --------------------------------------------------------------

echo
if [[ ${#FAILURES[@]} -eq 0 ]]; then
  log "Done — all components installed."
else
  fail "Done with ${#FAILURES[@]} component(s) failed: ${FAILURES[*]}"
  echo
  echo "If Chromium or Camoufox launches fail with missing system libraries, run ONCE with sudo:"
  echo "  sudo .venv-scrapling/bin/python -m playwright install-deps chromium"
  echo "or the equivalent on your distro (see https://playwright.dev/docs/cli#install-system-dependencies)."
  echo
  echo "Then re-run: make venvs"
fi

echo
echo "Next steps:"
echo "  make check          # verify everything is wired up"
echo "  claude              # open Claude Code; /crawl <URL> to run the thesis"

[[ ${#FAILURES[@]} -eq 0 ]] || exit 1
exit 0
