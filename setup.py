from setuptools import setup, find_packages

import taiga2

setup(
    name="taiga2",
    version=taiga2.__version__,
    packages=find_packages(),
    author="Remi Marenco",
    author_email="rmarenco@broadinstitute.org",
)
