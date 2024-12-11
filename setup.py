#!/usr/bin/env python3

import os

from setuptools import (
    setup,
    Extension
)

import numpy as np

BUILDING_EXT = os.environ.get('STOCK_PANDAS_BUILDING_EXT')

ext_kwargs = dict(
    # Ignore warning caused by cpython for using deprecated apis
    define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    include_dirs=[np.get_include()]
)

# Distribution ref
# https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#distributing-cython-modules
if BUILDING_EXT:
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

# When packaging the package, use the pre-compiled c++ file
else:
    extensions = [
        Extension(
            'stock_pandas.math._lib',
            ['stock_pandas/math/_lib.cpp'],
            **ext_kwargs
        )
    ]

# Only run setup when building the package
if __name__ == '__main__':
    setup(
        ext_modules=extensions,
        packages=[
            'stock_pandas',
            'stock_pandas.commands',
            'stock_pandas.directive',
            'stock_pandas.math',
            'stock_pandas.meta'
        ]
    )
