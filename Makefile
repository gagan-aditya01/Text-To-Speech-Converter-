.DEFAULT_GOAL := help

.PHONY: help setup run test test-unit test-integration lint clean \
        docker-build docker-run docker-stop docker-compose-up docker-compose-down

# ============================================================
# Help
# ============================================================
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Development
# ============================================================
setup: ## Create .venv and install all dependencies
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	cp -n .env.example .env || true
	mkdir -p outputs reports

run: ## Launch the Streamlit app (dev mode)
	.venv/bin/streamlit run app/main.py

# ============================================================
# Testing
# ============================================================
test: ## Run full test suite (unit + integration)
	mkdir -p reports
	.venv/bin/pytest tests/ -v --tb=short

test-unit: ## Run only unit tests (offline, fast)
	mkdir -p reports
	.venv/bin/pytest tests/ -m "not integration" -v --tb=short -q

test-integration: ## Run integration tests (real gTTS network calls)
	mkdir -p reports
	.venv/bin/pytest tests/ -m "integration" -v --tb=short

test-cov: ## Run unit tests with HTML coverage report
	mkdir -p reports
	.venv/bin/pytest tests/ -m "not integration" \
		--cov=app --cov-report=term-missing \
		--cov-report=html:reports/coverage

# ============================================================
# Lint
# ============================================================
lint: ## Run flake8 linter on app/ and tests/
	.venv/bin/python -m flake8 app/ tests/ \
		--max-line-length=100 \
		--extend-ignore=E203,W503 \
		--exclude=.venv,__pycache__

# ============================================================
# Docker
# ============================================================
docker-build: ## Build the Docker image (voicecraft:latest)
	docker build -t voicecraft:latest .

docker-run: ## Run the Docker container (port 8501)
	docker run --rm -p 8501:8501 \
		--env-file .env \
		--name voicecraft \
		voicecraft:latest

docker-stop: ## Stop the running container
	docker stop voicecraft 2>/dev/null || true

docker-compose-up: ## Start with Docker Compose (detached)
	docker compose up -d --build

docker-compose-down: ## Stop Docker Compose services
	docker compose down

# ============================================================
# Cleanup
# ============================================================
clean: ## Remove caches, pyc files, and generated audio
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf outputs/*.mp3 outputs/*.wav reports/
