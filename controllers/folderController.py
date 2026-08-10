from flask import request, jsonify
from marshmallow import ValidationError

from utils.error_handlers import ApiError, error_response, invalid_request_body_response, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.folderSchema import folder_schema, folders_schema

from services.folderService import folder_service, save as folder_service_save, find_user_folders as folder_service_find_user_folders, update as folder_service_update, delete as folder_service_delete


class FolderController:
  """Thin HTTP controller that delegates to an injected folder service."""

  def __init__(self, service=None, schema=None, folders_schema_obj=None):
    self._service = service or folder_service
    self._schema = schema or folder_schema
    self._folders_schema = folders_schema_obj or folders_schema

  @staticmethod
  def _apply_authenticated_user_id(payload, token_user_id):
    payload['user_id'] = int(token_user_id)
    return payload

  @token_required
  def save(self, user_id):
    try:
      folder_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    folder_data = self._apply_authenticated_user_id(folder_data, user_id)

    try:
      folder_save = self._service.save(user_id, folder_data)
      if folder_save is not None:
        return self._schema.jsonify(folder_save), 201
    except ApiError:
      raise
    except ValueError as e:
      error_message = str(e)
      lowered = error_message.lower()
      if 'unique' in lowered:
        return value_error_response(e, 409)
      if 'parent folder' in lowered and "doesn't exist" in lowered:
        return value_error_response(e, 404)
      return value_error_response(e, 400)
    except Exception:
      return internal_server_error_response()

  @token_required
  def find_user_folders(self, user_id):
    try:
      folders = self._service.find_user_folders(user_id)

      if folders is not None:
        return self._folders_schema.jsonify(folders), 200

      return error_response("Could not find any folders", 404)
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def update(self, user_id):
    try:
      folder_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    folder_data = self._apply_authenticated_user_id(folder_data, user_id)

    try:
      update_folder = self._service.update(user_id, folder_data)
      if update_folder is not None:
        return self._schema.jsonify(update_folder), 201
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def delete(self, user_id):
    try:
      folder_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    folder_data = self._apply_authenticated_user_id(folder_data, user_id)

    try:
      folder = self._service.delete(user_id, folder_data)

      if folder == "successful":
        return jsonify({"message": "Folder has be removed!"}), 200

      return error_response(f"Couldn't find folder '{folder_data['folder_name']}'", 404)
    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


folder_controller = FolderController()
folderService = folder_service


def save():
  return folder_controller.save()


def find_user_folders():
  return folder_controller.find_user_folders()


def update():
  return folder_controller.update()


def delete():
  return folder_controller.delete()