from flask import request, jsonify
from marshmallow import ValidationError

from utils.errorHandlers import ApiError, invalid_request_body_response, internal_server_error_response, value_error_response
from utils.utils import token_required, role_required

from models.schemas.roleSchema import role_schema, roles_schema

from services.roleService import role_service, save as role_service_save, find as role_service_find, update as role_service_update, delete as role_service_delete


class RoleController:
  """Thin HTTP controller that delegates to an injected role service."""

  def __init__(self, service=None, schema=None, roles_schema_obj=None):
    self._service = service or role_service
    self._schema = schema or role_schema
    self._roles_schema = roles_schema_obj or roles_schema

  @token_required
  @role_required('admin')
  def save(self, user_id=None):
    try:
      role_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    try:
      role_save = self._service.save(role_data)
      return self._schema.jsonify(role_save), 201
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  @role_required('admin')
  def find(self, user_id):
    try:
      roles = self._service.find(user_id)
      return self._roles_schema.jsonify(roles), 200
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  @role_required('admin')
  def update(self, user_id):
    try:
      role_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    try:
      updated_role = self._service.update(user_id, role_data)
      return self._schema.jsonify(updated_role), 201
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  @role_required('admin')
  def delete(self, user_id):
    try:
      role_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    try:
      deleted_role = self._service.delete(user_id, role_data)
      if deleted_role == 'successful':
        return jsonify({'message': "Role removed successfully"}), 200
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


role_controller = RoleController()
roleService = role_service


def save():
  return role_controller.save()


def find():
  return role_controller.find()


def update():
  return role_controller.update()


def delete():
  return role_controller.delete()