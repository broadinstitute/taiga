import os
import logging

log = logging.getLogger(__name__)

def load_config(app, settings_override=None, settings_file=None):
    app.config.from_object('taiga2.default_settings')
    if settings_override is not None:
        app.config.update(settings_override)
    elif settings_file is not None:
        if os.path.exists(settings_file):
            settings_file = os.path.abspath(settings_file)
            log.warning("Loading settings from %s", settings_file)
            app.config.from_pyfile(settings_file)
    else:
        if "TAIGA2_SETTINGS" in os.environ:
            settings_file = os.path.abspath(os.environ['TAIGA2_SETTINGS'])
            log.warning("Loading settings from (envvar TAIGA2_SETTINGS): %s", settings_file)
            app.config.from_pyfile(settings_file)
