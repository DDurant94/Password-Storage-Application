from flask import jsonify

from utils.errorHandlers import ApiError, internal_server_error_response, value_error_response
from utils.utils import token_required

from services.passwordGeneratorService import password_generator_service


class PasswordGeneratorController:
  """Thin HTTP controller that delegates to an injected password generator service."""

  def __init__(self, service=None):
    self._service = service or password_generator_service
    
  @staticmethod
  def _apply_authenticated_user_id(payload, token_user_id):
    payload['user_id'] = int(token_user_id)
    return payload
    
    
  @token_required
  def get(self, user_id):
    try:
      password = self._service.generate()
      return jsonify({'password': password}), 200
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


password_generator_controller = PasswordGeneratorController()
passwordGeneratorService = password_generator_service


def get():
  return password_generator_controller.get()