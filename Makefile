.PHONY: test lint check structural security clean install fix lines

# Install SDK in editable mode with dev tools
install:
	pip install -e ./sdk
	pip install pytest pytest-cov ruff

# Run full test suite with coverage
test:
	python -m pytest sdk/tests/ -v \
		--cov=agentguard \
		--cov-report=term-missing \
		--cov-fail-under=80

# Run only structural/architectural invariant tests
structural:
	python -m pytest sdk/tests/test_architecture.py -v

# Lint SDK source
lint:
	ruff check sdk/agentguard/

# Lint + auto-fix
fix:
	ruff check sdk/agentguard/ --fix

# Lint + full test suite (mirrors CI)
check: lint test

# Security lint (bandit)
security:
	bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q

# Clean build artifacts
clean:
	rm -rf sdk/dist/ sdk/build/ sdk/*.egg-info sdk/agentguard/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Show line counts per module (entropy check)
lines:
	@echo "=== Module Line Counts ==="
	@wc -l sdk/agentguard/*.py sdk/agentguard/sinks/*.py sdk/agentguard/integrations/*.py | sort -n
