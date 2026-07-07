#app.py
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from extensions import csrf, assets
from config import Config
from routes import register_routes
from utils import format_date_ddmmyyyy
from models import ensure_admin_exists
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.jinja_env.filters['datetime_format'] = format_date_ddmmyyyy
    app.config.from_object(Config)

    ensure_admin_exists()

    # Initialize extensions
    csrf.init_app(app)
    assets.init_app(app)

    # SCSS Bundle (optional)
    from flask_assets import Bundle
    scss = Bundle('style.scss', filters='libsass', output='style.css')
    assets.register('scss_all', scss)

    # Register blueprints/routes
    register_routes(app)

    @app.after_request
    def add_header(response):
        # Prevent browsers from caching pages so the back button doesn't reveal logged-in data
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)