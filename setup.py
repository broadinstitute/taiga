from setuptools import setup, find_packages

setup(
    name='taiga2',
    version='0.1',
    packages=['taiga2'],
    author="Philip Montgomery",
    author_email="pmontgom@broadinstitute.org",
    entry_points={'console_scripts': [
        "taiga2 = taiga2.app:main" ]}
)
