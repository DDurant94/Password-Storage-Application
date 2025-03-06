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
from routes.securityQuestionBP import security_question_blueprint

SWAGGER_URL = '/password-keeper-api/docs/'
API_URL = '/static/swagger.yaml'

swagger_blueprint = get_swaggerui_blueprint(
  SWAGGER_URL,
  API_URL,
  config={
    'app_name': 'Password Keeper'
  }
)


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
  app.register_blueprint(security_question_blueprint,url_prefix = '/security')
  app.register_blueprint(swagger_blueprint,url_prefix=SWAGGER_URL)
  
def configure_rate_limit():
  pass



if __name__ == "__main__":

  app = create_app("DevelopmentConfig")
  blue_print_config(app)
  configure_rate_limit()
  
  with app.app_context():
    db.create_all()
    
    
  app.run(debug=True)