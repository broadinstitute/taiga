from injector import inject, Injector
from flask import Flask, render_template, request, make_response, session, flash, redirect
from flask import Blueprint, abort
from flask import Config
import flask

import os
import logging
from sqlmeta import MetaStore, Hdf5Store
from convert import ConvertService,CacheService
import flask_injector
import ui
import rest

def handle_invalid_parameters(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def create_test_app(base_dir):
  app = Flask(__name__)

  app.config['SECRET_KEY'] = 'secret'
  app.config['TESTING'] = True
  app.config['DATA_DIR'] = base_dir
  app.config['ROOT_URL'] = "http://localhost"
  app.config['METADATA_PATH'] = base_dir+"/metadata.sqlite3"
  setup_app(app)

  return app

def setup_app(app):
  def configure_injector(binder):
    data_dir = app.config['DATA_DIR']
    metadata_path = app.config['METADATA_PATH']
    temp_dir = data_dir+"/temp"
    meta_store = MetaStore(metadata_path, data_dir+"/metadata.log")
    hdf5_store = Hdf5Store(data_dir)
    binder.bind(CacheService, to=CacheService(temp_dir))
    binder.bind(MetaStore, to=meta_store)
    binder.bind(Hdf5Store, to=hdf5_store)

  if "LOG_DIR" in app.config:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['LOG_DIR']+"/taiga.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
  
  app.errorhandler(rest.InvalidParameters)(handle_invalid_parameters)
  injector = Injector(configure_injector)
  flask_injector.init_app(app=app, injector=injector)
  ui.oid.init_app(app)
  ui.oid.after_login_func = injector.get(ui.create_or_login)
  app.register_blueprint(ui.ui)
  app.register_blueprint(rest.rest)
  flask_injector.post_init_app(app=app, injector=injector)

def create_app(taiga_config="~/.taiga/taiga.cfg"):
  log = logging.getLogger(__name__)
  app = Flask(__name__)
  app.config.from_object("taiga.default_config")
  config_override_path = os.path.expanduser(taiga_config)
  if os.path.exists(config_override_path):
    log.info("Loading config from %s" % config_override_path)
    app.config.from_pyfile(config_override_path)
  else:
    log.info("No file named %s.  Skipping" % config_override_path)
  setup_app(app)
  
  return app
