import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI =os.getenv('DATABASE_URL')#"postgresql://postgres:OcJOcgMFcnuFDXYSXbUzHltXaGnhHVBT@centerbeam.proxy.rlwy.net:40901/railway"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_SECURE = True  
    SESSION_COOKIE_HTTPONLY = True  
    PERMANENT_SESSION_LIFETIME = 3600  

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/data/products')

    PAYMENT_ENC_KEY="f6489d24c8c4a3f8cfd9292fe9fb57473099d6699699f68eb48500462e3fdbea"
    SERVER_NAME="salesta.store"
    PREFERRED_URL_SCHEME="https"
    FLASK_ENV="production"
