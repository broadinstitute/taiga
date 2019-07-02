from celery.bin.celery import main
import click
import subprocess
from flask.cli import with_appcontext

from .create_test_db_sqlalchemy import recreate_dev_db as _recreate_dev_db


@click.command()
@with_appcontext
def recreate_dev_db():
    _recreate_dev_db()


@click.command()
def webpack():
    subprocess.call(
        ["./node_modules/.bin/webpack", "--watch", "--mode=development"],
        cwd="react_frontend",
    )


@click.command()
@with_appcontext
def run_worker():
    """Starts a celery worker which will """
    main(
        [
            "",
            "-A",
            "taiga2",
            "worker",
            "-l",
            "info",
            "-E",
            "-n",
            "worker1@%h",
            "--max-memory-per-child",
            "200000",
        ]
    )
