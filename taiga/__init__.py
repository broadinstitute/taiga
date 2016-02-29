""" taiga application package """


def main():
  import argparse
  import taiga.app
  import os.path
  parser = argparse.ArgumentParser(description='Start Taiga.')
  parser.add_argument("config", help="path to config file")
  args = parser.parse_args()
  application = taiga.app.create_app(os.path.abspath(args.config))
  application.run(host='0.0.0.0', port=8999)
