from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from database import db
from schema import ma
from limiter import limiter
from caching import cache

from models.role import Role
from models.userManagement import UserManagementRole
from models.user import User
from models.passwords import Password
from models.passwordHist import PasswordHistory
from models.folder import Folder
from models.auditLog import AuditLog
from models.securityQuestion import SecurityQuestion

from routes.roleBP import role_blueprint
from routes.userBP import user_blueprint
from routes.folderBP import folder_blueprint
from routes.passwordBP import password_blueprint
from routes.passwordHistBP import password_history_blueprint
from routes.auditLogBP import audit_blueprint

def create_app(config_name):
  app = Flask(__name__)
  app.config.from_object(f"config.{config_name}")
  
  try:
    db.init_app(app)
    ma.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    CORS(app)
  except Exception as e:
    print(f"Error creating app: {e}")
    raise e

  return app

def blue_print_config(app):
  app.register_blueprint(user_blueprint,url_prefix = '/user')
  app.register_blueprint(role_blueprint,url_prefix = '/roles')
  app.register_blueprint(folder_blueprint,url_prefix = '/folder')
  app.register_blueprint(password_blueprint,url_prefix = '/password')
  app.register_blueprint(password_history_blueprint,url_prefix = '/history')
  app.register_blueprint(audit_blueprint,url_prefix = '/audit')
  
def configure_rate_limit():
  pass

app = create_app("DevelopmentConfig")
blue_print_config(app)
configure_rate_limit()

if __name__ == "__main__":

  
  with app.app_context():
    db.drop_all()
    db.create_all()
    
    
  app.run(debug=True)