.PHONY: install dev test coverage lint format clean build publish

# Install package
install:
	pip install -e .

# Install with dev dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run tests with coverage
coverage:
	pytest --cov=fastapi_autocrud_rishabh --cov-report=html --cov-report=term-missing

# Lint code
lint:
	flake8 fastapi_autocrud_rishabh tests
	mypy fastapi_autocrud_rishabh

# Format code
format:
	black fastapi_autocrud_rishabh tests examples
	isort fastapi_autocrud_rishabh tests examples

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete

# Build package
build: clean
	python -m build

# Publish to PyPI
publish: build
	python -m twine upload dist/*

# Publish to TestPyPI
publish-test: build
	python -m twine upload --repository testpypi dist/*

# Run basic example
run-basic:
	cd examples && python basic_example.py

# Run advanced example
run-advanced:
	cd examples && python advanced_example.py