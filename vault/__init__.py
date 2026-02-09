import os
from flask import Flask
# Added 'csrf' to the import list
from .extensions import db, login_manager, main_bp, csrf, mail 

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

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Initialize Migrate
    from .extensions import migrate
    migrate.init_app(app, db)

    # --- EMAIL CONFIGURATION ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    # ---------------------------
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Register Blueprints
        from .auth import auth_bp
        from .companies import companies_bp
        from .api import api_bp
        from .main import routes 

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp) 
        app.register_blueprint(companies_bp)
        app.register_blueprint(api_bp)

        # Build tables automatically (ONLY if they don't exist)
        from . import models
        try:
            db.create_all()
        except Exception as e:
            print(f"Table creation skipped or failed: {e}")

    # --- FIX FOR READ-ONLY FILE SYSTEM ---
    if os.environ.get('VERCEL'):
        # On Vercel, use the temporary folder provided by the OS
        upload_path = '/tmp'
    else:
        # On your laptop, keep using your local uploads folder
        upload_path = os.path.abspath(os.path.join(app.root_path, '..', 'uploads'))
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
    app.config['UPLOAD_FOLDER'] = upload_path

    return app