from flask import Flask
from config import Config

from extensions import db, bcrypt, csrf, limiter

# Blueprint
from routes.api_routes import api_bp
from routes.auth_routes import auth_bp


# Import model
from models import *

def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    app.config.from_object(Config)

    # Init Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )