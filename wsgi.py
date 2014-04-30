import taiga.ui

if __name__ == "__main__":
  app = taiga.ui.create_app()
  app.run(host='0.0.0.0', port=8999)
