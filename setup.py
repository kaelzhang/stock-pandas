
import os
from setuptools import setup

from stock_pandas import __version__


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(*fname):
    return open(os.path.join(os.path.dirname(__file__), *fname)).read()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


settings = dict(
    name='stock-pandas',
    packages=[
        'stock_pandas',
        'stock_pandas.commands',
        'stock_pandas.directive',
        'stock_pandas.math'
    ],
    version=__version__,
    author='Kael Zhang',
    author_email='i+pypi@kael.me',
    description='The wrapper of `pandas.DataFrame` with stock statistics and indicators support.',  # noqa:E501
    install_requires=read_requirements('requirements.txt'),
    tests_require=read_requirements('test-requirements.txt'),
    license='MIT',
    keywords='pandas pandas-dataframe stock stat indicators macd',
    url='https://github.com/kaelzhang/stock-pandas',
    long_description=read('docs', 'README.md'),
    long_description_content_type='text/markdown',
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
)

setup(**settings)
