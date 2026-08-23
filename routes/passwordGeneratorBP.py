from flask import Blueprint

from controllers.passwordGeneratorController import get


password_generator_blueprint = Blueprint('password_generator_bp', __name__)
password_generator_blueprint.route('/',methods=['GET'])(get)