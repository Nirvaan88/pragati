from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from .export import export_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(export_bp)
