# Makefile for the Yuho research paper.
#
# Targets:
#   make paper      — build main.pdf via latexmk (default).
#   make stats      — regenerate stats.tex from coverage.json.
#   make figures    — render Mermaid sources in figures/ to PDF + PNG.
#   make arxiv      — produce arxiv.tar.gz for upload.
#   make clean      — remove build artefacts.
#   make distclean  — also remove main.pdf.
#
# Requirements:
#   - latexmk (mactex / texlive)
#   - acmart.cls (texlive-latex-extra or via CTAN)
#   - mmdc (npm install -g @mermaid-js/mermaid-cli) for `make figures`
#   - python3 for `make stats` and `make arxiv`

PAPER       ?= main
BUILD_DIR   ?= build
COVERAGE     = ../library/penal_code/_coverage/coverage.json
STATS_TEX    = stats.tex
STATS_EXTRA  = stats-extra.tex
LATEXMK     ?= latexmk
LATEXMK_FLAGS = -lualatex -interaction=nonstopmode -halt-on-error \
                -output-directory=$(BUILD_DIR) -shell-escape

FIGURES_MMD := $(wildcard figures/*.mmd)
FIGURES_PDF := $(FIGURES_MMD:.mmd=.pdf)

.PHONY: paper smoke stats stats-extra figures arxiv clean distclean watch

paper: stats stats-extra $(FIGURES_PDF) | $(BUILD_DIR)
	$(LATEXMK) $(LATEXMK_FLAGS) $(PAPER).tex
	@cp $(BUILD_DIR)/$(PAPER).pdf ./$(PAPER).pdf
	@echo "Built $(PAPER).pdf"

# Smoke build using article class instead of acmart. No latexmk, no figures
# required, no acmart deps. Useful when basic TeX Live is the only install.
# Runs the full latex -> bibtex -> latex -> latex sequence so citations
# resolve to numbered references against references.bib.
smoke: stats stats-extra | $(BUILD_DIR)
	lualatex -interaction=nonstopmode -output-directory=$(BUILD_DIR) main_smoke.tex
	@cp references.bib $(BUILD_DIR)/
	cd $(BUILD_DIR) && bibtex main_smoke
	lualatex -interaction=nonstopmode -output-directory=$(BUILD_DIR) main_smoke.tex
	lualatex -interaction=nonstopmode -output-directory=$(BUILD_DIR) main_smoke.tex
	@cp $(BUILD_DIR)/main_smoke.pdf ./main_smoke.pdf
	@echo "Built main_smoke.pdf"

# Regenerate stats.tex from coverage.json. Safe to call repeatedly.
stats: $(STATS_TEX)

$(STATS_TEX): $(COVERAGE) scripts/gen_stats.py
	python3 scripts/gen_stats.py $(COVERAGE) > $(STATS_TEX)

# Regenerate stats-extra.tex (Table 1 SLOC) from the source tree.
stats-extra: $(STATS_EXTRA)

$(STATS_EXTRA): ../scripts/repo_stats.py
	python3 ../scripts/repo_stats.py > /dev/null

# Render every figures/*.mmd into figures/*.pdf via mmdc.
figures: $(FIGURES_PDF)

figures/%.pdf: figures/%.mmd
	mmdc -i $< -o $@ -b transparent || \
	  (echo "warning: mmdc not installed; skipping $<"; touch $@)

arxiv: paper
	@rm -f arxiv.tar.gz
	@cp $(BUILD_DIR)/$(PAPER).bbl ./$(PAPER).bbl 2>/dev/null || true
	tar --exclude='$(BUILD_DIR)' --exclude='*.aux' --exclude='*.log' \
	    --exclude='*.fls' --exclude='*.fdb_latexmk' --exclude='arxiv.tar.gz' \
	    --exclude='figures/*.mmd' --exclude='figures/*.pdf' --exclude='figures/*.png' \
	    -czf arxiv.tar.gz \
	    00README.XXX \
	    $(PAPER).tex $(PAPER).bbl \
	    sections/ figures/ \
	    references.bib stats.tex stats-extra.tex \
	    yuho-listing.sty \
	    methodology/methodology.tex \
	    2>/dev/null || true
	@echo "Wrote arxiv.tar.gz"

watch: stats
	$(LATEXMK) $(LATEXMK_FLAGS) -pvc $(PAPER).tex

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(PAPER).aux $(PAPER).log $(PAPER).out $(PAPER).bbl $(PAPER).blg \
	      $(PAPER).fls $(PAPER).fdb_latexmk $(PAPER).synctex.gz

distclean: clean
	rm -f $(PAPER).pdf $(STATS_TEX) figures/*.pdf arxiv.tar.gz
