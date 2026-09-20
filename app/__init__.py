from flask import Flask


def create_app():
    app = Flask(__name__)

    from .database import close_db, init_db
    from .routes import api

    app.teardown_appcontext(close_db)
    app.register_blueprint(api, url_prefix="/api")

    with app.app_context():
        init_db()

    return app
