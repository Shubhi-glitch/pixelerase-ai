from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app():

    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    app.config['SECRET_KEY'] = 'secret-key'

    # DATABASE
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Routes
    from app.routes.main_routes import main

    app.register_blueprint(main)

    with app.app_context():

        from app.models import ImageHistory

        db.create_all()

    return app