from flask import Flask
from flask_cors import CORS  # type: ignore
from flask_swagger_ui import get_swaggerui_blueprint  # type: ignore

from database import db
from schema import ma
from limiter import limiter
from caching import cache
from utils.errorHandlers import handle_api_error

SWAGGER_URL = '/password-keeper-api/docs/'
API_URL = '/static/swagger.yaml'


def create_app(config_name: str = "DevelopmentConfig") -> Flask:
    app = Flask(__name__)
    app.config.from_object(f"config.{config_name}")

    try:
        load_models()
        initialize_extensions(app)
    except Exception as e:
        print(f"Error creating app: {e}")
        raise e

    register_blueprints(app)
    app.register_error_handler(Exception, handle_api_error)
    return app


def load_models() -> None:
    from models.role import Role
    from models.userManagement import UserManagementRole
    from models.user import User
    from models.passwords import Password
    from models.passwordHist import PasswordHistory
    from models.folder import Folder
    from models.auditLog import AuditLog
    from models.securityQuestion import SecurityQuestion
    from models.refreshToken import RefreshToken

    _ = [Role, UserManagementRole, User, Password, PasswordHistory, Folder, AuditLog, SecurityQuestion, RefreshToken]


def initialize_extensions(app: Flask) -> None:
    db.init_app(app)
    ma.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    CORS(app)


def register_blueprints(app: Flask) -> None:
    from routes.roleBP import role_blueprint
    from routes.userBP import user_blueprint
    from routes.folderBP import folder_blueprint
    from routes.passwordBP import password_blueprint
    from routes.passwordGeneratorBP import password_generator_blueprint
    from routes.passwordHistBP import password_history_blueprint
    from routes.auditLogBP import audit_blueprint
    from routes.securityQuestionBP import security_question_blueprint

    swagger_blueprint = create_swagger_blueprint()

    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(role_blueprint, url_prefix='/roles')
    app.register_blueprint(folder_blueprint, url_prefix='/folder')
    app.register_blueprint(password_blueprint, url_prefix='/password')
    app.register_blueprint(password_generator_blueprint, url_prefix='/generate')
    app.register_blueprint(password_history_blueprint, url_prefix='/history')
    app.register_blueprint(audit_blueprint, url_prefix='/audit')
    app.register_blueprint(security_question_blueprint, url_prefix='/security')
    app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)


def create_swagger_blueprint():
    return get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': 'Password Keeper'}
    )


def configure_rate_limit() -> None:
    """Placeholder for future rate-limit configuration."""
    return None


app = create_app("DevelopmentConfig")


if __name__ == "__main__":
    configure_rate_limit()

    with app.app_context():
        # db.drop_all()
        db.create_all()

    app.run(debug=True)