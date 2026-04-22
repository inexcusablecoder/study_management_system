import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'study-system-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'study_system.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
