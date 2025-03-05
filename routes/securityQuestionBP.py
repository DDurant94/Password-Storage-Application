from flask import Blueprint

from controllers.securityQuestionController import save, find, update, delete

security_question_blueprint = Blueprint('security_question_bp', __name__)
security_question_blueprint .route('/',methods=['POST'])(save)
security_question_blueprint .route('/',methods=['GET'])(find)
security_question_blueprint .route('/',methods=['PUT'])(update)
security_question_blueprint .route('/',methods=['DELETE'])(delete)
