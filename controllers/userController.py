from flask import request, jsonify
from marshmallow import ValidationError

from utils.error_handlers import ApiError, handle_api_error
from utils.utils import token_required

from models.schemas.userSchema import user_schema

from services import userService


def save():
    user_data = user_schema.load(request.json)
    user_save = userService.save(user_data)

    if user_save is None:
        raise ApiError("Wait 10 seconds and try again!", status_code=400)

    return user_schema.jsonify(user_save), 201


@token_required
def find_by_id(user_id):
    user = userService.find_by_id(int(user_id))
    return user_schema.jsonify(user), 200


@token_required
def update(user_id):
    user_data = user_schema.load(request.json)
    updated_user = userService.update(user_data, user_id)

    if updated_user is None:
        raise ApiError("User update failed", status_code=400)

    return user_schema.jsonify(updated_user), 201


def login_user():
    user_data = request.json
    user = userService.login_user(user_data['username'], user_data['password'])

    if user[0]:
        return jsonify(user[0]), 200

    raise ApiError(f"Invalid {user[1]}", status_code=422)


@token_required
def delete(user_id):
    user = userService.delete(user_id)

    if user == "successful":
        return jsonify({"message": "User removed successfully"}), 200

    raise ApiError(f"Couldn't find User with ID {user_id}", status_code=404) 