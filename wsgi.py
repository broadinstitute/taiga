import taiga.app

if __name__ == "__main__":
  app = taiga.app.create_app()
  app.run(host='0.0.0.0', port=8999)
  
