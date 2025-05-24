from flask import Flask, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_talisman import Talisman
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
talisman = Talisman()

def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or 'config.Config')
    
    # Configure for production
    if not app.debug and not app.testing:
        app.config['SERVER_NAME'] = 'salesta.store'
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        
        # Security headers
        talisman.init_app(
            app,
            content_security_policy=None,
            force_https=True,
            strict_transport_security=True
        )
    else:
        # Local development configuration
        app.config['SERVER_NAME'] = 'localhost:5000'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Setup login view and messages
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Blueprints
    from app.auth.routes import auth_bp 
    from app.cart.routes import cart_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.payment.routes import payments_bp
    
    # Register main blueprints first
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register secure payment routes LAST
    app.register_blueprint(payments_bp)

    # User loader
    from app.admin.models import User, Category, Brand

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Product image serving
    @app.route('/products/<filename>')
    def product_image(filename):
        return send_from_directory('/data/products', filename)

    # Jinja filter
    def product_image_url(img):
        try:
            if img and img.image_path:
                filename = img.image_path.rsplit('/', 1)[-1]
                return url_for('product_image', filename=filename)
        except Exception:
            pass
        return url_for('static', filename='images/default.jpg')

    app.jinja_env.filters['product_image_url'] = product_image_url

    # Global template variables
    @app.context_processor
    def inject_globals():
        return {
            'categories': Category.query.order_by(Category.name).all(),
            'brands': Brand.query.order_by(Brand.name).all()   
        }
    
    return app