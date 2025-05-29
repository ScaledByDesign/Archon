# Production RAG System - Testing Makefile

.PHONY: test test-unit test-integration test-component test-scripts test-all test-coverage clean-test

# Default Python interpreter
PYTHON := python3

# Test directories
TEST_DIR := tests
UNIT_DIR := $(TEST_DIR)/unit
INTEGRATION_DIR := $(TEST_DIR)/integration
COMPONENT_DIR := $(TEST_DIR)/component
SCRIPTS_DIR := $(TEST_DIR)/scripts

# Coverage settings
COV_DIR := htmlcov
COV_REPORT := coverage.xml

# Default target
test: test-unit

# Run all unit tests
test-unit:
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest $(UNIT_DIR) -v --tb=short

# Run all integration tests
test-integration:
	@echo "🔗 Running integration tests..."
	$(PYTHON) -m pytest $(INTEGRATION_DIR) -v --tb=short -m "not slow"

# Run all component tests
test-component:
	@echo "🔧 Running component tests..."
	$(PYTHON) -m pytest $(COMPONENT_DIR) -v --tb=short

# Run script-based tests
test-scripts:
	@echo "📜 Running script-based tests..."
	@for script in $(SCRIPTS_DIR)/*.sh; do \
		echo "Running $$script..."; \
		chmod +x $$script; \
		$$script || exit 1; \
	done
	@for script in $(SCRIPTS_DIR)/*.py; do \
		echo "Running $$script..."; \
		$(PYTHON) $$script || exit 1; \
	done

# Run all tests
test-all: test-unit test-component test-integration
	@echo "✅ All Python tests completed"

# Run tests with coverage
test-coverage:
	@echo "📊 Running tests with coverage..."
	$(PYTHON) -m pytest $(TEST_DIR) --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

# Run slow tests (marked with @pytest.mark.slow)
test-slow:
	@echo "🐌 Running slow tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v -m "slow"

# Run tests that require Docker services
test-docker:
	@echo "🐳 Running Docker-dependent tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -v -m "requires_docker"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest $(FILE) -v

# Run tests matching a pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_function_name"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest $(TEST_DIR) -v -k "$(PATTERN)"

# Install test dependencies
install-test-deps:
	@echo "📦 Installing test dependencies..."
	$(PYTHON) -m pip install -r requirements.txt

# Lint test code
lint-tests:
	@echo "🔍 Linting test code..."
	$(PYTHON) -m flake8 $(TEST_DIR) --max-line-length=88
	$(PYTHON) -m black --check $(TEST_DIR)

# Format test code
format-tests:
	@echo "🎨 Formatting test code..."
	$(PYTHON) -m black $(TEST_DIR)

# Clean test artifacts
clean-test:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf $(COV_DIR)
	rm -f $(COV_REPORT)
	rm -rf .pytest_cache
	rm -rf $(TEST_DIR)/__pycache__
	rm -rf $(TEST_DIR)/*/__pycache__
	find $(TEST_DIR) -name "*.pyc" -delete

# Show test structure
show-tests:
	@echo "📁 Test structure:"
	@tree $(TEST_DIR) || find $(TEST_DIR) -type f -name "*.py" | sort

# Validate test setup
validate-tests:
	@echo "✅ Validating test setup..."
	@echo "Checking pytest configuration..."
	@test -f pytest.ini && echo "✓ pytest.ini found" || echo "✗ pytest.ini missing"
	@echo "Checking test directories..."
	@test -d $(UNIT_DIR) && echo "✓ Unit tests directory found" || echo "✗ Unit tests directory missing"
	@test -d $(INTEGRATION_DIR) && echo "✓ Integration tests directory found" || echo "✗ Integration tests directory missing"
	@test -d $(COMPONENT_DIR) && echo "✓ Component tests directory found" || echo "✗ Component tests directory missing"
	@test -d $(SCRIPTS_DIR) && echo "✓ Scripts tests directory found" || echo "✗ Scripts tests directory missing"
	@echo "Checking conftest files..."
	@test -f $(TEST_DIR)/conftest.py && echo "✓ Main conftest.py found" || echo "✗ Main conftest.py missing"

# Help
help:
	@echo "Available test commands:"
	@echo "  test              - Run unit tests only"
	@echo "  test-unit         - Run unit tests"
	@echo "  test-integration  - Run integration tests"
	@echo "  test-component    - Run component tests"
	@echo "  test-scripts      - Run script-based tests"
	@echo "  test-all          - Run all Python tests"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-slow         - Run slow tests"
	@echo "  test-docker       - Run Docker-dependent tests"
	@echo "  test-file         - Run specific test file (FILE=path)"
	@echo "  test-pattern      - Run tests matching pattern (PATTERN=name)"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  lint-tests        - Lint test code"
	@echo "  format-tests      - Format test code"
	@echo "  clean-test        - Clean test artifacts"
	@echo "  show-tests        - Show test directory structure"
	@echo "  validate-tests    - Validate test setup"
