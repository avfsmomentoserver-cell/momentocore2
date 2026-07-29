.PHONY: help install dev test lint format clean build run-api run-worker docker-up docker-down migrate

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest $(TEST_OPTIONS)

lint: ## Run linters
	flake8 core agents services tests
	black --check core agents services tests
	mypy core agents services

format: ## Format code with black and isort
	black core agents services tests
	isort core agents services tests

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build dist htmlcov .coverage

build: ## Build the package
	python -m build

run-api: ## Run the FastAPI server
	uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

run-worker: ## Run the background worker
	python -m services.workers.consumer

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	alembic upgrade head

migrate-revision: ## Create a new migration
	alembic revision --autogenerate -m "$(MESSAGE)"

seed: ## Seed database with sample data
	python -m core.data_core.storage.seed

monitor: ## Open Grafana dashboard
	@echo "Opening Grafana at http://localhost:3001"
	open http://localhost:3001 || xdg-open http://localhost:3001

docs: ## Generate documentation
	mkdocs serve

health: ## Check system health
	curl -f http://localhost:8000/health || echo "API not running"
