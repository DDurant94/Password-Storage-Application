from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.passwordSchema import password_schema, passwords_schema

from services import passwordService

@token_required
def save(user_id):
  try:
    password_data = password_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400

  try:
    password_save = passwordService.save(user_id,password_data)
    return password_schema.jsonify(password_save), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400

@token_required
def find_passwords(user_id): 
  try:
    passwords = passwordService.find_passwords(user_id)
    if passwords is not None:
      return passwords_schema.jsonify(passwords), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400

@token_required
def find_password(user_id,name):
  try:
    passwords = passwordService.find_password(user_id,name)
    if passwords is not None:
      return password_schema.jsonify(passwords), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400

@token_required
def update(user_id):
  try:
    password_data = password_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400

  try:
    password_updated = passwordService.update(user_id,password_data)

    return password_schema.jsonify(password_updated), 201
    
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400

@token_required 
def delete(user_id):
  try:
    password_data = password_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    password = passwordService.delete(user_id,password_data)
    
    if password == "successful":
      return jsonify({"message": "Password has be removed!"}), 200
    
    else:
      return jsonify({"message": f"Couldn't find Password '{password_data['password_name']}'"}), 404
    
  except ValueError as e:
    return jsonify({'Error': str(e)}), 400