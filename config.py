import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super_secret_key')  # Use environment variable or fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///comps.db')  # Use env variable if set
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable modification tracking for better performance