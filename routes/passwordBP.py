from flask import Blueprint

from controllers.passwordController import save, find_passwords, find_password, update, delete

password_blueprint = Blueprint('password_bp', __name__)
password_blueprint.route('/',methods=['POST'])(save)
password_blueprint.route('/',methods=['GET'])(find_passwords)
password_blueprint.route('/<string:name>',methods=['GET'])(find_password)
password_blueprint.route('/',methods=['PUT'])(update)
password_blueprint.route('/',methods=['DELETE'])(delete)
