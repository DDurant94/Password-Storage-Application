from typing import Any

from flask import Flask, jsonify, has_app_context
from marshmallow import ValidationError


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload: dict[str, Any] | None = None, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
        self.error_code = error_code


INVALID_REQUEST_BODY_MESSAGE = "Invalid request body"
INTERNAL_SERVER_ERROR_MESSAGE = "Internal server error"


def _json_error_response(message: str, status_code: int, details: dict[str, Any] | None = None, error_code: str | None = None):
    payload: dict[str, Any] = {"status": "error", "message": message}
    if error_code:
        payload["error_code"] = error_code
    if details:
        payload["details"] = details

    if has_app_context():
        return jsonify(payload), status_code

    app = Flask(__name__)
    with app.app_context():
        return jsonify(payload), status_code


def error_response(message: str, status_code: int = 400, details: dict[str, Any] | None = None, error_code: str | None = None):
    return _json_error_response(message, status_code, details, error_code)


def invalid_request_body_response():
    return error_response(INVALID_REQUEST_BODY_MESSAGE, 400, error_code="invalid_request")


def internal_server_error_response():
    return error_response(INTERNAL_SERVER_ERROR_MESSAGE, 500, error_code="internal_server_error")


def _infer_error_details(message: str):
    lower_message = message.lower()
    if "already exists" in lower_message or "already in database" in lower_message:
        return "user_already_exists", {
            "code": "user_already_exists",
            "domain": "user",
            "operation": "create",
            "message": "The requested user already exists.",
        }
    if "invalid password" in lower_message:
        return "invalid_password", {
            "code": "invalid_password",
            "domain": "user",
            "operation": "create",
            "message": "The provided password does not meet the validation requirements.",
        }
    if "role not found" in lower_message:
        return "role_not_found", {
            "code": "role_not_found",
            "domain": "role",
            "operation": "lookup",
            "message": "The requested role could not be found.",
        }
    if "user not found" in lower_message or "user not found!" in lower_message:
        return "user_not_found", {
            "code": "user_not_found",
            "domain": "user",
            "operation": "lookup",
            "message": "The requested user could not be found.",
        }
    if "folder not found" in lower_message or "couldn't find folder" in lower_message:
        return "folder_not_found", {
            "code": "folder_not_found",
            "domain": "folder",
            "operation": "lookup",
            "message": "The requested folder could not be found.",
        }
    if "question not found" in lower_message:
        return "question_not_found", {
            "code": "question_not_found",
            "domain": "security_question",
            "operation": "lookup",
            "message": "The requested security question could not be found.",
        }
    if "couldn't find password" in lower_message or "password not found" in lower_message:
        return "password_not_found", {
            "code": "password_not_found",
            "domain": "password",
            "operation": "lookup",
            "message": "The requested password could not be found.",
        }
    if "not found" in lower_message or "couldn't find" in lower_message:
        return "not_found", {
            "code": "not_found",
            "domain": "resource",
            "operation": "lookup",
            "message": "The requested resource could not be found.",
        }
    if "can not delete" in lower_message or "cannot delete" in lower_message or "protected" in lower_message:
        return "delete_forbidden", {
            "code": "delete_forbidden",
            "domain": "resource",
            "operation": "delete",
            "message": "The requested resource cannot be deleted.",
        }
    return None, None


def value_error_response(error: ValueError, status_code: int = 422, error_code: str | None = None):
    message = str(error)
    inferred_code, inferred_details = _infer_error_details(message)
    if error_code is None:
        error_code = inferred_code
    if inferred_details is not None:
        return error_response(message, status_code, details=inferred_details, error_code=error_code)
    return error_response(message, status_code, error_code=error_code)


def handle_api_error(error: Exception):
    if isinstance(error, ApiError):
        details = error.payload if error.payload else None
        return error_response(error.message, error.status_code, details, error.error_code)

    if isinstance(error, ValidationError):
        validation_details = error.messages
        if isinstance(validation_details, dict):
            details = validation_details
        else:
            details = {"messages": validation_details}
        return error_response("Validation failed", 400, details, error_code="validation_failed")

    if isinstance(error, ValueError):
        inferred_code, inferred_details = _infer_error_details(str(error))
        return error_response(str(error), 422, details=inferred_details, error_code=inferred_code or "validation_failed")

    return error_response(INTERNAL_SERVER_ERROR_MESSAGE, 500, error_code="internal_server_error")
