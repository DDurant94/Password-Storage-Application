from flask import Blueprint

from controllers.roleController import save

role_blueprint = Blueprint('role_bp', __name__)
role_blueprint.route('/',methods =['POST'])(save)