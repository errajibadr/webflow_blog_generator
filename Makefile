# Website SEO Orchestrator Makefile
#
# Usage examples:
#   make run SITE=your-site
#   make export SITE=your-site
#   make dry-run SITE=your-site
#   make configure-credentials SITE=your-site

.PHONY: run export generate enrich import dry-run verbose list-backends set-backend-file set-backend-env list-credentials configure-credentials add-credential test-credential install

# Default configuration
CONFIG=config.yaml

# Ensure SITE is provided for website-specific commands
check-site:
ifndef SITE
	$(error SITE is required. Usage: make [command] SITE=your-site)
endif

# Run the full pipeline
run: check-site
	python main.py --website $(SITE) --all

# Run the export step
export: check-site
	python main.py --website $(SITE) --export

# Run the generate step
generate: check-site
	python main.py --website $(SITE) --generate

# Run the enrich step
enrich: check-site
	python main.py --website $(SITE) --enrich

# Run the import step
import: check-site
	python main.py --website $(SITE) --import

# Run in dry-run mode (no changes)
dry-run: check-site
	python main.py --website $(SITE) --all --dry-run

# Run with verbose logging
verbose: check-site
	python main.py --website $(SITE) --all --verbose

# List available credential backends
list-backends:
	python main.py --credential-backend list

# Set credential backend to file
set-backend-file:
	python main.py --credential-backend file

# Set credential backend to environment variables
set-backend-env:
	python main.py --credential-backend env

# List all credentials
list-credentials:
	python main.py --credential list

# Configure credentials interactively
configure-credentials: check-site
	python main.py --credential configure --website-cred $(SITE) --interactive

# Add a specific credential
add-credential: check-site
ifndef TYPE
	$(error TYPE is required. Usage: make add-credential SITE=your-site TYPE=FTP_USERNAME VALUE=yourusername)
endif
ifdef VALUE
	python main.py --credential add --website-cred $(SITE) --type $(TYPE) --value "$(VALUE)"
else
	python main.py --credential add --website-cred $(SITE) --type $(TYPE) --interactive
endif

# Test credentials
test-credential: check-site
	python main.py --credential test --website-cred $(SITE)

# Remove a credential
remove-credential: check-site
ifndef TYPE
	$(error TYPE is required. Usage: make remove-credential SITE=your-site TYPE=FTP_USERNAME)
endif
	python main.py --credential remove --website-cred $(SITE) --type $(TYPE) --force

# Install dependencies
install:
	pip install -r requirements.txt

# Clean build files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/

# Create default directories
init:
	mkdir -p logs
	mkdir -p workspaces
	mkdir -p website_configs
	@echo "Directory structure created"

# Help
help:
	@echo "Website SEO Orchestrator Commands:"
	@echo ""
	@echo "Pipeline Commands:"
	@echo "  make run SITE=your-site             Run full pipeline"
	@echo "  make export SITE=your-site          Export website"
	@echo "  make generate SITE=your-site        Generate content"
	@echo "  make enrich SITE=your-site          Enrich website"
	@echo "  make import SITE=your-site          Import website"
	@echo "  make dry-run SITE=your-site         Run in dry-run mode"
	@echo "  make verbose SITE=your-site         Run with verbose logging"
	@echo ""
	@echo "Credential Commands:"
	@echo "  make list-backends                  List available credential backends"
	@echo "  make set-backend-file               Use file-based credential backend"
	@echo "  make set-backend-env                Use environment-based credential backend"
	@echo "  make list-credentials               List all credentials"
	@echo "  make configure-credentials SITE=your-site    Configure credentials interactively"
	@echo "  make add-credential SITE=your-site TYPE=FTP_USERNAME VALUE=value    Add credential"
	@echo "  make add-credential SITE=your-site TYPE=FTP_PASSWORD               Add credential interactively"
	@echo "  make test-credential SITE=your-site Test credentials"
	@echo "  make remove-credential SITE=your-site TYPE=FTP_USERNAME           Remove credential"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install                        Install dependencies"
	@echo "  make clean                          Clean build files"
	@echo "  make init                           Create default directories"
	@echo ""
	@echo "For more information, see README.md" 