from flask import jsonify
from marshmallow import ValidationError


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


def handle_api_error(error: Exception):
    if isinstance(error, ApiError):
        response_payload = {"message": error.message, **error.payload}
        return jsonify(response_payload), error.status_code

    if isinstance(error, ValidationError):
        return jsonify({"errors": error.messages}), 400

    if isinstance(error, ValueError):
        return jsonify({"error": str(error)}), 422

    return jsonify({"error": "Internal server error"}), 500
