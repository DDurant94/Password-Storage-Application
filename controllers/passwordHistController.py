from flask import jsonify, request

from utils.errorHandlers import error_response, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.passwordHistSchema import password_histories_schema

from services.passwordHistService import password_history_service, find_passwords_history as password_hist_service_find_passwords_history, find_password_history as password_hist_service_find_password_history, delete as password_hist_service_delete


class PasswordHistoryController:
  """Thin HTTP controller that delegates to an injected password-history service."""

  def __init__(self, service=None, schema=None):
    self._service = service or password_history_service
    self._schema = schema or password_histories_schema

  @token_required
  def all_passwords_hist(self, user_id):
    try:
      limit = request.args.get('limit', default=50, type=int)
      offset = request.args.get('offset', default=0, type=int)
      limit = max(1, min(limit, 100))
      offset = max(0, offset)
      all_history = self._service.find_passwords_history(user_id, limit=limit, offset=offset)

      if all_history == []:
        return jsonify({'message': 'No password History'}), 404

      if all_history is not None:
        return self._schema.jsonify(all_history), 200
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def password_hist_by_name(self, user_id, search_name):
    try:
      limit = request.args.get('limit', default=50, type=int)
      offset = request.args.get('offset', default=0, type=int)
      limit = max(1, min(limit, 100))
      offset = max(0, offset)
      history = self._service.find_password_history(user_id, search_name, limit=limit, offset=offset)
      if history == []:
        return error_response(f"No password History for '{search_name}'", 404)

      if history is not None:
        return self._schema.jsonify(history), 200
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


password_history_controller = PasswordHistoryController()
passwordHistService = password_history_service


def all_passwords_hist():
  return password_history_controller.all_passwords_hist()


def password_hist_by_name(search_name):
  return password_history_controller.password_hist_by_name(search_name=search_name)
  