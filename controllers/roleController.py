from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.roleSchema import role_schema, roles_schema

from services import roleService

def save():
  try:
    role_data = role_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    role_save = roleService.save(role_data)
    return role_schema.jsonify(role_save), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400