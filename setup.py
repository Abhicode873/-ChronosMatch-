from Cython.Build import cythonize
from setuptools import Extension, setup

extensions = [
    Extension(
        "chronosmatch.core.cython_order_book",
        ["src/chronosmatch/core/cython_order_book.pyx"],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        build_dir="build/cython",
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
        },
    )
)