#!/usr/bin/env python3

import os

from setuptools import (
    setup,
    Extension
)

import numpy as np

# beta version
__version__ = '0.25.7'


BUILDING = os.environ.get('STOCK_PANDAS_BUILDING')


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(*fname) -> str:
    if not BUILDING:
        return '<README.md>'

    return open(os.path.join(os.path.dirname(__file__), *fname)).read()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


ext_kwargs = dict(
    # Ignore warning caused by cpython for using deprecated apis
    define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    include_dirs=[np.get_include()]
)

# Distribution ref
# https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#distributing-cython-modules
if BUILDING:
    from Cython.Build import cythonize
    extensions = cythonize(
        Extension(
            'stock_pandas.math._lib',
            ['stock_pandas/math/_lib.pyx'],
            language='c++',
            **ext_kwargs
        ),
        compiler_directives={
            'linetrace': False,
            'language_level': 3
        }
    )
else:
    extensions = [
        Extension(
            'stock_pandas.math._lib',
            ['stock_pandas/math/_lib.cpp'],
            **ext_kwargs
        )
    ]


settings = dict(
    name='stock-pandas',
    packages=[
        'stock_pandas',
        'stock_pandas.commands',
        'stock_pandas.directive',
        'stock_pandas.math'
    ],
    ext_modules=extensions,
    zip_safe=False,
    version=__version__,
    author='Kael Zhang',
    author_email='i+pypi@kael.me',
    description='The wrapper of `pandas.DataFrame` with stock statistics and indicators support.',  # noqa:E501
    install_requires=[
        'numpy >= 1.16.5',
        'pandas >= 1.0.0'
    ],
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


if __name__ == '__main__':
    setup(**settings)
