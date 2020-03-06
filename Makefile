test:
	pytest -s -v test/test_*.py --doctest-modules --cov stock_pandas --cov-config=.coveragerc --cov-report term-missing

lint:
	flake8 stock_pandas test

install:
	pip install -r requirements.txt -r test-requirements.txt

report:
	codecov

build: stock_pandas
	rm -rf dist
	python setup.py sdist bdist_wheel

publish:
	make build
	twine upload --config-file ~/.pypirc -r pypi dist/*

.PHONY: test
