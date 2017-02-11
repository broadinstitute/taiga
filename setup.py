from setuptools import setup, find_packages

import taiga2

setup(
    name='taiga2',
    version=taiga2.__version__,
    packages=find_packages(),
    author="Philip Montgomery",
    author_email="pmontgom@broadinstitute.org",
    entry_points={'console_scripts': [
        "taiga2 = taiga2.main:main"]},
    install_requires=[
        'attrs==16.2.0',
        'connexion==1.0.129',
        'boto3==1.4.2',
        'Flask==0.11.1',
        'celery==4.0.0',
        'connexion==1.0.129',
        'redis==2.10.5',
        'requests==2.11.0',
        'six==1.10.0',
        'SQLAlchemy==1.1.4',
        'Flask-SQLAlchemy==2.1',
        'marshmallow-sqlalchemy==0.12.1',
        'flask-marshmallow==0.7.0',
        'marshmallow-enum==1.0',
        'marshmallow-oneofschema==1.0.3',
        'pytest==3.0.5',
        'freezegun==0.3.8',
        'python-magic==0.4.12',
        'h5py==2.6.0',
        'numpy==1.11.3',
        'psycopg2==2.6.2'
    ],
)
