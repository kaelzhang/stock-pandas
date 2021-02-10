files = stock_pandas test *.py
test_files = *
# test_files = manipulate

test:
	pytest -s -v test/test_$(test_files).py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

lint:
	flake8 $(files)

fix:
	autopep8 --in-place -r $(files)

install:
	pip install -U -r requirements.txt -r test-requirements.txt -r docs/requirements.txt

report:
	codecov

build: stock_pandas
	rm -rf dist
	make build-ext
	python setup.py sdist bdist_wheel

build-ext:
	STOCK_PANDAS_BUILDING=1 python setup.py build_ext --inplace

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
