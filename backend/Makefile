.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
SERVICE_NAME="travel_ai_backend"

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@if [ "$(USING_POETRY)" ]; then poetry env info && exit; fi
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)python -V
	@$(ENV_PREFIX)python -m site

.PHONY: install
install:          ## Install the project in dev mode.
	@DEPENDENCIES=all; 
	@POETRY_OPTS="";
	if [ "$(USING_POETRY)" ]; then \
		if [ "$$DEPENDENCIES" = "all" ]; then \
			echo "Installing all dependencies..."; \
			poetry install --with dev; \
			poetry install --with test; \
			exit; \
		else \
			echo "Installing specific dependencies..."; \
			poetry install --with $$DEPENDENCIES; \
		fi; \
	else \
		echo "Don't forget to run 'make virtualenv' if you got errors."; \
		pip install -e .[test]; \
	fi

.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)isort $(SERVICE_NAME)/
	$(ENV_PREFIX)black $(SERVICE_NAME)/
	$(ENV_PREFIX)black tests/


.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 $(SERVICE_NAME)/
	$(ENV_PREFIX)black --check $(SERVICE_NAME)/
	$(ENV_PREFIX)black --check tests/
	$(ENV_PREFIX)mypy --ignore-missing-imports $(SERVICE_NAME)/
	$(ENV_PREFIX)pydocstyle $(SERVICE_NAME)/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -v --cov-config .coveragerc --cov=$(SERVICE_NAME) -l --tb=short --maxfail=1 tests/
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr $(ENV_PREFIX)pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: virtualenv
virtualenv:       ## Create a virtual environment.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	@echo "creating virtualenv ..."
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@./.venv/bin/pip install -e .[test]
	@echo
	@echo "!!! Please run 'source .venv/bin/activate' to enable the environment !!!"

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > $(SERVICE_NAME)/VERSION
	@$(ENV_PREFIX)gitchangelog > HISTORY.md
	@git add $(SERVICE_NAME)/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: docs
docs:
	@echo "building documentation ..."
	@rm -rf docs/build
	@find docs/source/ -type f -name '*.rst' ! -name 'index.rst' -delete
	@$(ENV_PREFIX)sphinx-apidoc -f -o docs/source $(SERVICE_NAME)/
	@$(ENV_PREFIX)sphinx-build -b html docs/source  docs/build/html

.PHONY: switch-to-poetry
switch-to-poetry: ## Switch to poetry package manager.
	@echo "Switching to poetry ..."
	@if ! poetry --version > /dev/null; then echo 'poetry is required, install from https://python-poetry.org/'; exit 1; fi
	@rm -rf .venv
	@poetry init --no-interaction --name=a_flask_test --author=rochacbruno
	@echo "" >> pyproject.toml
	@echo "[tool.poetry.scripts]" >> pyproject.toml
	@echo "$(SERVICE_NAME) = '$(SERVICE_NAME).__main__:main'" >> pyproject.toml
	@cat requirements.txt | while read in; do poetry add --no-interaction "$${in}"; done
	@cat requirements-test.txt | while read in; do poetry add --no-interaction "$${in}" --dev; done
	@poetry install --no-interaction
	@mkdir -p .github/backup
	@mv requirements* .github/backup
	@mv setup.py .github/backup
	@echo "You have switched to https://python-poetry.org/ package manager."
	@echo "Please run 'poetry shell' or 'poetry run $(SERVICE_NAME)'"

.PHONY: init
init:             ## Initialize the project based on an application template.
	@./.github/init.sh
	