files = stock_pandas test *.py
test_files = *
# test_files = cum_append

export STOCK_PANDAS_BUILDING = 1
export STOCK_PANDAS_UPLOADING = 1

test:
	STOCK_PANDAS_COW=1 pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

lint:
	ruff check $(files)

fix:
	ruff check --fix $(files)

install:
	pip install -U .[dev]
	pip install -U -r docs/requirements.txt

report:
	codecov

build: stock_pandas
	rm -rf dist
	make build-ext
	python setup.py sdist bdist_wheel

build-ext:
	python setup.py build_ext --inplace

# Used to test build_ext without cython
build-ext-no-cython:
	python setup.py build_ext --inplace

build-doc:
	sphinx-build -b html docs build_docs

upload:
	twine upload --config-file ~/.pypirc -r pypi dist/*

publish:
	make build
	make upload

.PHONY: test build
