from setuptools import setup, find_packages

setup(
    name='taiga',
    version='1.0',
    packages=['taiga'],
    install_requires=["numpy", "scipy", "Flask==0.10.1", "Flask-Injector==0.3.1", "Flask-SQLAlchemy==1.0", "Jinja2==2.7.2", "SQLAlchemy==0.9.4", 
        "alembic==0.6.4", "gunicorn==18.0", "h5py==2.2.1", "injector==0.8.0", "nose==1.3.0", "requests==2.2.1", "Flask-OpenID==1.2.1", "markdown==2.4.1"],
    author="Philip Montgomery",
    author_email="pmontgom@broadinstitute.org",
    long_description="A tool for sharing tabular and matrix datasets"
)
