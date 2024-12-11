files = stock_pandas test *.py
test_files = *
# test_files = cum_append

export

test:
	STOCK_PANDAS_COW=1 pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

lint:
	@echo "Running ruff..."
	@ruff check $(files)
	@echo "Running mypy..."
	@mypy $(files)

fix:
	ruff check --fix $(files)

install:
	pip install -U .[dev]
	pip install -U -r docs/requirements.txt

report:
	codecov

build: stock_pandas
	rm -rf dist build
	make build-ext
	python -m build --sdist --wheel

build-ext:
	STOCK_PANDAS_BUILDING=1 python setup.py build_ext --inplace

build-doc:
	sphinx-build -b html docs build_docs

upload:
	twine upload --config-file ~/.pypirc -r pypi dist/*

publish:
	make build
	make upload

.PHONY: test build
