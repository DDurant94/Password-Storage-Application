from flask import Blueprint

from controllers.auditLogController import find

audit_blueprint = Blueprint('audit_log_bp', __name__)
audit_blueprint.route('/',methods= ['GET'])(find)