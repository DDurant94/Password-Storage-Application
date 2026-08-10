from flask import request, jsonify
from marshmallow import ValidationError

from utils.error_handlers import ApiError, error_response, invalid_request_body_response, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.userSchema import user_schema

from services.userService import user_service, save as user_service_save, find_by_id as user_service_find_by_id, update as user_service_update, login_user as user_service_login_user, refresh_user_token as user_service_refresh_user_token, revoke_refresh_token as user_service_revoke_refresh_token, revoke_all_refresh_tokens as user_service_revoke_all_refresh_tokens, delete as user_service_delete


class UserController:
    """Thin HTTP controller that delegates to an injected service."""

    def __init__(self, service=None, schema=None):
        self._service = service or user_service
        self._schema = schema or user_schema

    def save(self):
        try:
            user_data = self._schema.load(request.get_json(silent=True))
        except ValidationError as err:
            return jsonify(err.messages), 400
        except Exception:
            return invalid_request_body_response()

        try:
            user_save = self._service.save(user_data)
        except ApiError:
            raise
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

        if user_save is None:
            raise ApiError("Wait 10 seconds and try again!", status_code=400)

        return self._schema.jsonify(user_save), 201

    @token_required
    def find_by_id(self, user_id):
        try:
            user = self._service.find_by_id(int(user_id))
            return self._schema.jsonify(user), 200
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

    @token_required
    def update(self, user_id):
        try:
            user_data = self._schema.load(request.get_json(silent=True))
        except ValidationError as err:
            return jsonify(err.messages), 400
        except Exception:
            return invalid_request_body_response()

        try:
            updated_user = self._service.update(user_data, user_id)
        except ApiError:
            raise
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

        if updated_user is None:
            raise ApiError("User update failed", status_code=400)

        return self._schema.jsonify(updated_user), 201

    def login_user(self):
        try:
            user_data = request.get_json(silent=True) or {}
            user = self._service.login_user(user_data.get('username'), user_data.get('password'))
        except ApiError:
            raise
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

        if user[0]:
            return jsonify(user[0]), 200

        raise ApiError(f"Invalid {user[1]}", status_code=422)

    def refresh_user_token(self):
        user_data = request.get_json(silent=True) or {}
        refresh_token = user_data.get('refresh_token')
        if not refresh_token:
            return error_response("refresh_token is required", 400)

        try:
            refreshed = self._service.refresh_user_token(refresh_token)
            return jsonify(refreshed), 200
        except ApiError:
            raise
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

    def logout_user(self):
        user_data = request.get_json(silent=True) or {}
        refresh_token = user_data.get('refresh_token')
        if not refresh_token:
            return error_response("refresh_token is required", 400)

        try:
            result = self._service.revoke_refresh_token(refresh_token)
            return jsonify(result), 200
        except ApiError:
            raise
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

    @token_required
    def logout_all_user_sessions(self, user_id):
        try:
            result = self._service.revoke_all_refresh_tokens(user_id)
            return jsonify(result), 200
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

    @token_required
    def delete(self, user_id):
        try:
            user = self._service.delete(user_id)
        except ValueError as err:
            return value_error_response(err)
        except Exception:
            return internal_server_error_response()

        if user == "successful":
            return jsonify({"message": "User removed successfully"}), 200

        raise ApiError(f"Couldn't find User with ID {user_id}", status_code=404)


user_controller = UserController()
userService = user_service


def save():
    return user_controller.save()


def find_by_id():
    return user_controller.find_by_id()


def update():
    return user_controller.update()


def login_user():
    return user_controller.login_user()


def refresh_user_token():
    return user_controller.refresh_user_token()


def logout_user():
    return user_controller.logout_user()


def logout_all_user_sessions():
    return user_controller.logout_all_user_sessions()


def delete():
    return user_controller.delete()