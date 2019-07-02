#!/usr/bin/env python

from flask_script import Manager, Command
from flask_migrate import MigrateCommand

from taiga2.api_app import create_only_flask_app

"""Uses Flask Manager to handle some application managements:

- db init/migrate/upgrade (for Alembic, more infos with db --help
"""
manager = Manager(create_only_flask_app)
manager.add_option("-c", "--config", dest="settings_file", required=False)
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
