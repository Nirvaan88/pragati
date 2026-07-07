#forms.py
from flask_wtf import FlaskForm

class CSRFOnlyForm(FlaskForm):
    """Form used to validate CSRF token for basic POST actions."""
    pass
