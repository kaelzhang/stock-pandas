files = stock_pandas test *.py
test_files = *
# test_files = parser
# test_files = commands
# test_files = cum_append

.PHONY: test lint fix install report build clean build-pkg build-ext build-doc upload publish install-rust test-rust test-python test-all test-coverage benchmark

# Install all dependencies (Python + Rust)
install:
	@echo "\033[1m>> Installing Rust toolchain... <<\033[0m"
	@which rustup > /dev/null || curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	@rustup update stable
	@echo "\033[1m>> Installing maturin... <<\033[0m"
	@pip install maturin
	@echo "\033[1m>> Installing Python dependencies... <<\033[0m"
	@pip install -e .[dev]

# Install only Rust toolchain
install-rust:
	@echo "\033[1m>> Installing Rust toolchain... <<\033[0m"
	@which rustup > /dev/null || curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	@rustup update stable

# Build the Rust extension and Python package
build: clean
	@echo "\033[1m>> Building Rust extension... <<\033[0m"
	@maturin develop --release
	@echo "\033[1m>> Build complete! <<\033[0m"

# Build release package (wheel and sdist)
build-pkg: clean
	@echo "\033[1m>> Building release package... <<\033[0m"
	@maturin build --release
	@echo "\033[1m>> Package built in target/wheels/ <<\033[0m"

# Build the Rust extension only (development mode)
build-ext:
	@echo "\033[1m>> Building Rust extension (dev mode)... <<\033[0m"
	@maturin develop

# Clean build artifacts
clean:
	rm -rf dist build target/wheels
	rm -rf stock_pandas/*.so
	rm -rf stock_pandas/math/*.so
	rm -rf stock_pandas/math/*.cpp
	rm -rf *.egg-info
	rm -rf .eggs
	rm -rf __pycache__
	rm -rf .coverage .coverage.* htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Run tests with Rust backend (default)
test:
	STOCK_PANDAS_COW=1 pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

# Run tests with Python backend only
test-python:
	@echo "\033[1m>> Running tests with Python backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=python pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report=

# Run tests with Rust backend only
test-rust:
	@echo "\033[1m>> Running tests with Rust backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=rust pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report=

# Run tests with both backends and merge coverage (for 100% coverage)
test-coverage:
	@echo "\033[1m>> Running tests with Python backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=python pytest -s test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report=
	@mv .coverage .coverage.python
	@echo "\033[1m>> Running tests with Rust backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=rust pytest -s test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report=
	@mv .coverage .coverage.rust
	@echo "\033[1m>> Merging coverage reports... <<\033[0m"
	coverage combine .coverage.python .coverage.rust
	coverage report --show-missing
	@rm -f .coverage.python .coverage.rust

# Run tests for all backends (alias for test-coverage)
test-all: test-coverage

# Run tests with verbose output
test-verbose:
	STOCK_PANDAS_COW=1 pytest -s -vv test/test_$(test_files).py --doctest-modules

# Run Rust unit tests
cargo-test:
	cargo test

# Run linter
lint:
	@echo "\033[1m>> Running ruff... <<\033[0m"
	@ruff check $(files)
	@echo "\033[1m>> Running mypy... <<\033[0m"
	@mypy $(files)
	@echo "\033[1m>> Running cargo check... <<\033[0m"
	@cargo check

# Auto-fix linting issues
fix:
	ruff check --fix $(files)
	cargo fmt

# Format Rust code
fmt:
	cargo fmt

# Check Rust code
check:
	cargo check
	cargo clippy

# Run benchmark tests
benchmark:
	@echo "\033[1m>> Running benchmarks... <<\033[0m"
	STOCK_PANDAS_COW=1 pytest test/test_benchmark.py -v --benchmark-only --benchmark-columns=mean,stddev,median,ops

# Run benchmark comparing Rust vs Python
benchmark-compare:
	@echo "\033[1m>> Benchmarking Python backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=python pytest test/test_benchmark.py -v --benchmark-only --benchmark-save=python --benchmark-columns=mean,stddev,median,ops
	@echo "\033[1m>> Benchmarking Rust backend... <<\033[0m"
	STOCK_PANDAS_COW=1 STOCK_PANDAS_BACKEND=rust pytest test/test_benchmark.py -v --benchmark-only --benchmark-save=rust --benchmark-columns=mean,stddev,median,ops
	@echo "\033[1m>> Comparing results... <<\033[0m"
	pytest-benchmark compare .benchmarks/*python* .benchmarks/*rust* --columns=mean,stddev,median,ops

# Build documentation
build-doc:
	sphinx-build -b html docs build_docs

# Upload to PyPI
upload:
	twine upload --config-file ~/.pypirc -r pypi target/wheels/*

# Publish (build + upload)
publish:
	make build-pkg
	make upload

# Report coverage
report:
	codecov

# Development workflow: build and test
dev: build test

# Full CI check
ci: lint cargo-test test-coverage
