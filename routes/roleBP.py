from flask import Blueprint

from controllers.roleController import save, find, update, delete

role_blueprint = Blueprint('role_bp', __name__)
role_blueprint.route('/',methods =['POST'])(save)
role_blueprint.route('/',methods=['GET'])(find)
role_blueprint.route('/',methods=['PUT'])(update)
role_blueprint.route('/',methods=['DELETE'])(delete)