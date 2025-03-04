from flask import Blueprint

from controllers.passwordHistController import all_passwords_hist, password_hist_by_name

password_history_blueprint = Blueprint('password_history_bp', __name__)
password_history_blueprint.route('/',methods=['GET'])(all_passwords_hist)
password_history_blueprint.route('/search=<string:search_name>',methods=['GET'])(password_hist_by_name)
