.DEFAULT_GOAL := help

REQUIREMENTS_DIR = requirements
reqbases = $(wildcard $(REQUIREMENTS_DIR)/*.in)
objects = $(patsubst %.in,%.txt,$(reqbases))

$(REQUIREMENTS_DIR)/%.txt: $(REQUIREMENTS_DIR)/%.in $(reqbases)
	pip-compile $<

.PHONY: requirements
requirements: $(objects) ## Compile requirements with pip-compile

.PHONY: upgrade-requirements
upgrade-requirements: ## Upgrade and compile requirements with pip-compile --upgrade
	for file in $(REQUIREMENTS_DIR)/*.in; do \
		pip-compile --upgrade $$file; \
	done

.PHONY: sync-requirements
sync-requirements: ## Install development python dependencies and clean dangling dependencies from environment
	pip-sync $(REQUIREMENTS_DIR)/dev.txt

.PHONY: translations
translations: ## Regenerate .po files with ./manage.py makemessages
	./manage.py makemessages -a -i "requirements/*" -i "virtualization/*"

.PHONY: compile-translations
compile-translations: ## Compile .po files with ./manage.py compilemessages
	./manage.py compilemessages -l fr -l de

.PHONY: format
format:  # Fix some linting issues in the project
	black apps defivelo fabfile.py
	isort apps defivelo fabfile.py

.PHONY: lint
lint:  # Show linting issues in the project
	flake8 apps defivelo fabfile.py

.PHONY: help
help: ## Display this help
	@grep -E '^[.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -k 1,1 | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
