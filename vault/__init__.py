import os
from flask import Flask
# Added 'csrf' to the import list
from .extensions import db, login_manager, main_bp, csrf 

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- CLOUD DEPLOYMENT HARDWIRING ---
    # Use Vercel Environment Variables if they exist, otherwise use local defaults
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix: Vercel/Neon often provide 'postgres://', but SQLAlchemy needs 'postgresql://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to your local instance folder database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/vault.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # -----------------------------------

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)  # <--- Initializes the CSRF protection
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Register Blueprints
        from .auth.routes import auth_bp
        from .companies.routes import companies_bp
        from .main import routes 

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp) 
        app.register_blueprint(companies_bp)

        # Build tables automatically (works for both local and cloud)
        from . import models
        db.create_all()

    # Handle Uploads Folder
    upload_path = os.path.abspath(os.path.join(app.root_path, '..', 'uploads'))
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    app.config['UPLOAD_FOLDER'] = upload_path

    return app