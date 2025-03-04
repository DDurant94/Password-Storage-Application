from flask import Blueprint

from controllers.folderController import save, find_user_folders, update, delete

folder_blueprint = Blueprint('folder_bp', __name__)
folder_blueprint.route('/', methods = ['POST'])(save)
folder_blueprint.route('/',methods= ['GET'])(find_user_folders)
folder_blueprint.route('/',methods= ['PUT'])(update)
folder_blueprint.route('/',methods= ['DELETE'])(delete)