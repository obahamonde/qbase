# type: ignore
from Cython.Build import cythonize
from setuptools import Extension, setup

ext_modules = [
    Extension(
        "qbase",
        sources=["qbase.pyx"],
        include_dirs=["/usr/local/include"],
        library_dirs=["/usr/local/lib"],
        libraries=["rocksdb"],
        extra_compile_args=["-std=c++17"],
        language="c++",
    )
]

setup(
    name="rocksdb",
    ext_modules=cythonize(ext_modules),
)