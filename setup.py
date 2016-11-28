from setuptools import setup, find_packages

import taiga2

#required
#attrs (16.2.0)
#connexion (2016.0.dev1, /Users/pmontgom/dev/connexion)
#Flask (0.11.1)
#requests (2.11.0)
#six (1.10.0)
#tinydb (3.2.1)

setup(
    name='taiga2',
    version=taiga2.__version__,
    packages=find_packages(),
    author="Philip Montgomery",
    author_email="pmontgom@broadinstitute.org",
    entry_points={'console_scripts': [
        "taiga2 = taiga2.app:main" ]},
    install_requires=[
        'attrs==16.2.0',
        'connexion>=1.0.129',
        'Flask==0.11.1',
        'requests==2.11.0',
        'six==1.10.0',
        'tinydb==3.2.1',
    ],
)
