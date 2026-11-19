import os

from flask import Flask
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from model import db, User
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.admin_routes import admin_bp
from routes.examiner_routes import examiner_bp
from routes.student_routes import student_bp
from routes.job_routes import jobs_bp
from utils.errors import register_error_handlers
import utils.cache 


def create_app():
    app = Flask(__name__)

    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'emp-dev-secret-key-change-me-in-production-0123456789')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}

    JWTManager(app)
    CORS(app)
    db.init_app(app)

    for bp in (auth_bp, api_bp, admin_bp, examiner_bp, student_bp, jobs_bp):
        app.register_blueprint(bp)

    register_error_handlers(app)

    with app.app_context():
        init_db()

    return app


def init_db():
    """Create tables programmatically and seed the single admin account."""
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email=os.environ.get('ADMIN_EMAIL', 'admin@gmail.com'),
            password=generate_password_hash(os.environ.get('ADMIN_PASSWORD', '1111')),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
