.DEFAULT_GOAL := help

.PHONY: help setup run test lint clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	cp -n .env.example .env || true
	mkdir -p outputs

run: ## Launch the Streamlit app
	.venv/bin/streamlit run app/main.py

test: ## Run all tests with coverage report
	.venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Lint the codebase with ruff
	.venv/bin/ruff check app/ tests/

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov outputs/*.mp3 outputs/*.wav
