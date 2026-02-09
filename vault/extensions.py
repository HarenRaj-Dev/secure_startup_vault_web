from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask import Blueprint
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
main_bp = Blueprint("main", __name__)
csrf = CSRFProtect()
mail = Mail()