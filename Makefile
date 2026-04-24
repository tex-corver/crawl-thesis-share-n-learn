# share_learn_research — Makefile
#
# Installs / verifies the Python venvs + Node deps the /crawl skill needs.
# All targets are idempotent.

.DEFAULT_GOAL := help
SHELL := bash

.PHONY: help venvs check clean clean-venvs slides

help:   ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} \
		/^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "First-time setup:  make venvs && make check"
	@echo "Then:              claude   (inside the repo, try: /crawl <URL>)"

venvs:  ## Install all 4 Python venvs + npm deps (idempotent)
	@bash scripts/setup.sh

check:  ## Verify all required tools are present — fails if anything is missing
	@bash scripts/check.sh

clean-venvs:  ## Remove all .venv-* directories (careful — destructive)
	@echo "Removing .venv-scrapy .venv-scrapling .venv-crawl4ai .venv-r3"
	@rm -rf .venv-scrapy .venv-scrapling .venv-crawl4ai .venv-r3
	@echo "Done. Run 'make venvs' to reinstall."

clean:  ## Remove slidev build artefacts (safe — leaves venvs alone)
	@rm -rf dist .slidev-cache

slides: ## Start the slidev dev server at :3030
	@npm run dev
