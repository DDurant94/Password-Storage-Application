from dotenv import load_dotenv
import os

load_dotenv()
PASSWORD = os.getenv('PASSWORD')

class Config:
    """Base configuration with shared settings."""
    CACHE_TYPE = 'SimpleCache'

class DevelopmentConfig(Config):
    """Development environment configuration."""
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://root:{PASSWORD}@localhost/PasswordKeeper'
    DEBUG = True

class TestingConfig(Config):
    """Testing environment configuration."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory DB for tests
    TESTING = True
    DEBUG = False