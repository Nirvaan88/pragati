#extensions.py
from flask_wtf import CSRFProtect
from flask_assets import Environment

csrf = CSRFProtect()
assets = Environment()