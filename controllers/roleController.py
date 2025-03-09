from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.roleSchema import role_schema, roles_schema

from services import roleService

@token_required
@role_required('admin')
def save():
  try:
    role_data = role_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    role_save = roleService.save(role_data)
    return role_schema.jsonify(role_save), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422
  
@token_required
@role_required('admin')
def find(user_id):
  try:
    roles = roleService.find(user_id)
    return roles_schema.jsonify(roles), 200
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422

@token_required
@role_required('admin')
def update(user_id):
  try:
    role_data = role_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    updated_role = roleService.update(user_id,role_data)
    return role_schema.jsonify(updated_role), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422
  
@token_required
@role_required('admin')
def delete(user_id):
  try:
    role_data = role_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    deleted_role = roleService.delete(user_id,role_data)
    if deleted_role == 'successful':
      return jsonify({'message': "Role removed successfully"}), 200
    
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422