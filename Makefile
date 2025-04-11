# Default website name (can be overridden via command line)
WEBSITE ?= sample

# Python command
PYTHON = uv run

# Main script
SCRIPT = main.py

# Config directory
CONFIG_DIR = website_configs

# Help target
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make [target] [WEBSITE=website_name]"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Run all website generation tasks for specified website"
	@echo "  clean      - Clean generated files"
	@echo "  help       - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make all                    - Run all tasks for default website ($(WEBSITE))"
	@echo "  make all WEBSITE=dogtolib   - Run all tasks for dogtolib website"
	@echo "  make clean WEBSITE=dogtolib - Clean dogtolib generated files"

# All target - runs the full website generation
.PHONY: all
all:
	@echo "Generating website for $(WEBSITE)..."
	$(PYTHON) $(SCRIPT) --website $(WEBSITE) --all

# Clean target - removes generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files for $(WEBSITE)..."
	rm -rf build/$(WEBSITE)
	rm -rf dist/$(WEBSITE)

# Default target
.DEFAULT_GOAL := help 