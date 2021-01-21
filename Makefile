files = stock_pandas test *.py
test_files = test_*.py

test:
	pytest -s -v test/$(test_files) --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

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
	python setup.py sdist bdist_wheel

build-ext:
	python setup.py build_ext --inplace

build-doc:
	sphinx-build -b html docs build_docs

publish:
	make build
	twine upload --config-file ~/.pypirc -r pypi dist/*

.PHONY: test build
