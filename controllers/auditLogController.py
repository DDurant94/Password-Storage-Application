from flask import jsonify, request
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.auditLogSchema import audit_log_schema, audit_logs_schema

from services import auditLogService

@token_required
def find(user_id):  
  try:
    logs = auditLogService.find(user_id)
    if logs is not None:
      return audit_logs_schema.jsonify(logs), 200
  
  except ValueError as e:
    return jsonify({"Error": str(e)}),400