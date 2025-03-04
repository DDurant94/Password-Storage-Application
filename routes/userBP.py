from flask import Blueprint

from controllers.userController import save, find_by_id, update, login_user, delete

user_blueprint = Blueprint('user_bp', __name__)
user_blueprint.route('/',methods=['POST'])(save)
user_blueprint.route('/',methods=['GET'])(find_by_id)
user_blueprint.route('/',methods=['PUT'])(update)
user_blueprint.route('/login',methods=['POST'])(login_user)
user_blueprint.route('/',methods = ['DELETE'])(delete)
