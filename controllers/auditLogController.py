from flask import jsonify, request

from utils.errorHandlers import ApiError, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.auditLogSchema import audit_logs_schema

from services.auditLogService import audit_log_service, find as audit_log_find, save as audit_log_save, finder as audit_log_finder


class AuditLogController:
  """Thin HTTP controller that delegates to an injected audit-log service."""

  def __init__(self, service=None, schema=None):
    self._service = service or audit_log_service
    self._schema = schema or audit_logs_schema

  @token_required
  def find(self, user_id):
    try:
      limit = request.args.get('limit', default=50, type=int)
      offset = request.args.get('offset', default=0, type=int)
      limit = max(1, min(limit, 100))
      offset = max(0, offset)
      logs = self._service.find(user_id, limit=limit, offset=offset)
      if logs is not None:
        return self._schema.jsonify(logs), 200
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


audit_log_controller = AuditLogController()
auditLogService = audit_log_service


def find():
  return audit_log_controller.find()