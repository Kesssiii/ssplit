from pathlib import Path

from flask import Flask, send_file


def create_app():
    app = Flask(__name__)

    from .database import close_db, init_db
    from .routes import api

    app.teardown_appcontext(close_db)
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/api/docs")
    def api_docs():
        swagger_ui_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>ssplit API Docs</title>
          <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css" />
          <style>
            html, body {
              margin: 0;
              background: #f5f7fb;
              font-family: Arial, sans-serif;
            }
            #swagger-ui {
              max-width: 1200px;
              margin: 20px auto;
              padding: 0 20px 40px;
            }
          </style>
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
          <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-standalone-preset.js"></script>
          <script>
            window.onload = () => {
              SwaggerUIBundle({
                url: '/api/openapi.yaml',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                layout: 'BaseLayout'
              });
            };
          </script>
        </body>
        </html>
        """
        return swagger_ui_html

    @app.get("/api/openapi.yaml")
    def api_openapi_yaml():
        spec_path = Path(__file__).resolve().parent.parent / "openeapi.yml"
        return send_file(spec_path, mimetype="application/yaml")

    with app.app_context():
        init_db()

    return app
