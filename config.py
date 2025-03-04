from dotenv import load_dotenv
import os

load_dotenv()
PASSWORD = os.getenv('PASSWORD')

class DevelopmentConfig:
  SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://root:{PASSWORD}@localhost/PasswordKeeper'
  CACHE_TYPE = 'SimpleCache'
  DEBUG = True