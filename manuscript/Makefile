# manuscript/Makefile -- builds the ICSE 2027 SEIP paper (main.tex).
# The submitted APSEC paper lives in apsec/ and has its own `make apsec` target.
# `make` with no target lists the targets.
.DEFAULT_GOAL := help
.PHONY: help draft paper submit check arms titles section watch tables tables-smoke overleaf apsec clean

# --- Switches (override on the command line: make draft ARM=reduced) -------
ARM          ?= full
MODE         ?= draft
TITLE        ?= A
TABLES       ?= tables
BUNDLE       ?=
VERA_FOUNDRY ?= ../../Foundry-experiences/vera-foundry
PYTHON       ?= python3
STRICT       ?=

BUILD  := build
GITREV := $(shell git rev-parse --short HEAD 2>/dev/null || echo no-git)$(shell git diff --quiet HEAD -- . 2>/dev/null || echo +dirty)
DATE   := $(shell date +%Y-%m-%d)

# One job name per variant, so the variants never share an .aux file.
JOB := main$(if $(filter-out full,$(ARM)),-$(ARM))$(if $(filter-out draft,$(MODE)),-$(MODE))$(if $(filter-out A,$(TITLE)),-title$(TITLE))$(if $(filter-out tables,$(TABLES)),-$(notdir $(TABLES)))
PRETEX := \def\icsearm{$(ARM)}\def\icsemode{$(MODE)}\def\icsetitle{$(TITLE)}\def\icsetables{$(TABLES)}\def\icsegitrev{$(GITREV)}\def\icsebuilddate{$(DATE)}
LATEXMK := latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=$(BUILD)
CHECK := $(PYTHON) scripts/check.py --job $(BUILD)/$(JOB) --tables $(TABLES) --mode $(MODE) $(if $(STRICT),--strict)

help: ## List the targets and switches
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Switches: ARM=full|reduced|withdrawn  MODE=draft|clean|submit  TITLE=A|B|C"
	@echo "            TABLES=<dir of generated tables>  BUNDLE=<vera-foundry replication zip>"

draft: ## Build the paper with the drafting cockpit, and print the page report
	@mkdir -p $(BUILD)
	$(LATEXMK) -jobname=$(JOB) -usepretex='$(PRETEX)' main.tex
	@cp $(BUILD)/$(JOB).pdf $(JOB).pdf
	@$(CHECK) --brief
	@echo "PDF: manuscript/$(JOB).pdf"

paper: ## Build the paper alone, without cockpit or plan markers
	@$(MAKE) --no-print-directory draft MODE=clean

submit: ## Submission build: fails on any placeholder, smoke table, APSEC number or limit breach
	@$(MAKE) --no-print-directory draft MODE=submit
	@$(MAKE) --no-print-directory check MODE=submit STRICT=1

check: ## Full report on the last build of this variant (pages, budgets, guards, fonts)
	@$(CHECK)

arms: ## Build the three ML-arm scenarios
	@for a in full reduced withdrawn; do $(MAKE) --no-print-directory draft ARM=$$a || exit 1; done

titles: ## Build the three title options (the title block height differs)
	@for t in A B C; do $(MAKE) --no-print-directory draft TITLE=$$t || exit 1; done

section: ## Build one section file with the full preamble (S=06b-fairness)
	@test -n "$(S)" || { echo "S is required: make section S=04-vera"; exit 2; }
	@mkdir -p $(BUILD)
	$(LATEXMK) -jobname=section-$(S)-$(ARM) -usepretex='$(PRETEX)\def\icseonly{$(S)}' main.tex
	@echo "PDF: manuscript/$(BUILD)/section-$(S)-$(ARM).pdf"

watch: ## Rebuild the draft on every save
	@mkdir -p $(BUILD)
	$(LATEXMK) -pvc -jobname=$(JOB) -usepretex='$(PRETEX)' main.tex

tables: ## Regenerate tables/ and figures/ from a vera-foundry bundle (BUNDLE=...zip)
	@test -n "$(BUNDLE)" || { echo "BUNDLE is required: make tables BUNDLE=path/to/vera-foundry-replication-<date>.zip"; exit 2; }
	cd $(VERA_FOUNDRY) && .venv/bin/vera-foundry paper tables --bundle $(abspath $(BUNDLE)) --out $(CURDIR)
	cd $(VERA_FOUNDRY) && .venv/bin/vera-foundry paper figures --bundle $(abspath $(BUNDLE)) --out $(CURDIR)

tables-smoke: ## Wire-test the generated tables with vera-foundry's smoke results (stamped SMOKE DATA)
	@rm -rf tables-smoke && mkdir -p tables-smoke
	cp $(VERA_FOUNDRY)/results-smoke/paper/tables/*.tex tables-smoke/
	@$(MAKE) --no-print-directory draft TABLES=tables-smoke

overleaf: ## Zip the sources for an Overleaf project (build/overleaf.zip)
	@mkdir -p $(BUILD)
	@rm -f $(BUILD)/overleaf.zip
	zip -qr $(BUILD)/overleaf.zip main.tex support sections floats references.bib IEEEtran.cls IEEEtran.bst \
		$(wildcard tables) $(wildcard figures) $(wildcard authors.tex)
	@echo "Overleaf defaults: ARM=full MODE=draft TITLE=A (edit support/preamble.tex to change)"

apsec: ## Build the submitted APSEC paper (apsec/main_apsec.pdf)
	cd apsec && latexmk -pdf -interaction=nonstopmode -outdir=build main_apsec.tex && cp build/main_apsec.pdf main_apsec.pdf
	@echo "PDF: manuscript/apsec/main_apsec.pdf"

clean: ## Remove every build product
	rm -rf $(BUILD) apsec/build tables-smoke main*.pdf apsec/main_apsec.pdf
