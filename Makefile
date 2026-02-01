# Makefile for Learn AI Agents project
# Provides convenient commands for development workflow

.PHONY: sync install clean format lint type-check verify test test-unit test-verbose test-specific

# Dependencies
sync:
	uv sync

install:
	uv add $(PKG)

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info

# Code Quality
format:
	uv run ruff check --select I --fix src/
	uv run ruff format src/

lint:
	uv run ruff check src/

type-check:
	uv run mypy src/learn_ai_agents/

verify: format lint type-check
	@echo "✓ Code verification complete!"

# Testing
test:
	@echo "Running all tests..."
	cd src/learn_ai_agents && python -m unittest discover -s tests -p "test_*.py" -v

test-unit:
	@echo "Running unit tests..."
	cd src/learn_ai_agents && python -m unittest discover -s tests/unit -p "test_*.py" -v

test-verbose:
	@echo "Running tests with verbose output..."
	cd src/learn_ai_agents && python -m unittest discover -s tests -p "test_*.py" -v --locals

test-specific:
	@echo "Running specific test: $(TEST)"
	cd src/learn_ai_agents && python -m unittest $(TEST) -v

test-coverage:
	@echo "Running tests with coverage..."
	cd src/learn_ai_agents && python -m coverage run -m unittest discover -s tests -p "test_*.py"
	cd src/learn_ai_agents && python -m coverage report -m
	cd src/learn_ai_agents && python -m coverage html
	@echo "Coverage report generated in src/learn_ai_agents/htmlcov/index.html"