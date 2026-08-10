from flask import Blueprint

from controllers.userController import save, find_by_id, update, login_user, refresh_user_token, logout_user, logout_all_user_sessions, delete

user_blueprint = Blueprint('user_bp', __name__)
user_blueprint.route('/',methods=['POST'])(save)
user_blueprint.route('/',methods=['GET'])(find_by_id)
user_blueprint.route('/',methods=['PUT'])(update)
user_blueprint.route('/login',methods=['POST'])(login_user)
user_blueprint.route('/refresh',methods=['POST'])(refresh_user_token)
user_blueprint.route('/logout',methods=['POST'])(logout_user)
user_blueprint.route('/logout-all',methods=['POST'])(logout_all_user_sessions)
user_blueprint.route('/',methods = ['DELETE'])(delete)
