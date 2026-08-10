from flask import request, jsonify
import math
from marshmallow import ValidationError

from utils.error_handlers import ApiError, error_response, invalid_request_body_response, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.passwordSchema import password_schema, passwords_schema

from services.passwordService import password_service, save as password_service_save, find_passwords as password_service_find_passwords, find_password as password_service_find_password, update as password_service_update, delete as password_service_delete, finder as password_service_finder


class PasswordController:
  """Thin HTTP controller that delegates to an injected password service."""

  def __init__(self, service=None, schema=None, passwords_schema_obj=None):
    self._service = service or password_service
    self._schema = schema or password_schema
    self._passwords_schema = passwords_schema_obj or passwords_schema

  @staticmethod
  def _apply_authenticated_user_id(payload, token_user_id):
    payload['user_id'] = int(token_user_id)
    return payload

  @token_required
  def save(self, user_id):
    try:
      password_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    password_data = self._apply_authenticated_user_id(password_data, user_id)

    try:
      password_save = self._service.save(user_id, password_data)
      return self._schema.jsonify(password_save), 201
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def find_passwords(self, user_id):
    try:
      limit = request.args.get('limit', default=50, type=int)
      offset = request.args.get('offset', default=0, type=int)
      limit = max(1, min(limit, 100))
      offset = max(0, offset)

      passwords = self._service.find_passwords(user_id, limit=limit, offset=offset)
      if passwords is not None:
        return self._passwords_schema.jsonify(passwords), 200
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def find_password(self, user_id, name):
    try:
      passwords = self._service.find_password(user_id, name)
      if passwords is not None:
        return self._schema.jsonify(passwords), 200

      return jsonify({'message': f"Couldn't find '{name}'"}), 404

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def update(self, user_id):
    try:
      password_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    password_data = self._apply_authenticated_user_id(password_data, user_id)

    try:
      password_updated = self._service.update(user_id, password_data)
      return self._schema.jsonify(password_updated), 201

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def delete(self, user_id):
    try:
      password_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    password_data = self._apply_authenticated_user_id(password_data, user_id)

    try:
      password = self._service.delete(user_id, password_data)

      if password == "successful":
        return jsonify({"message": "Password has be removed!"}), 200

      return error_response(f"Couldn't find Password '{password_data['password_name']}'", 404)

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


password_controller = PasswordController()
passwordService = password_service


def save():
  return password_controller.save()


def find_passwords():
  return password_controller.find_passwords()


def find_password(name):
  return password_controller.find_password(name=name)


def update():
  return password_controller.update()


def delete():
  return password_controller.delete()