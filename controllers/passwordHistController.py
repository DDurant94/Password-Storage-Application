from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.utils import token_required, role_required

from models.schemas.passwordHistSchema import password_histories_schema, password_history_schema

from services import passwordHistService

# Getting all Password History controller (for user)
@token_required
def all_passwords_hist(user_id):  
  try:
    all_history = passwordHistService.find_passwords_history(user_id)
    
    if all_history == []:
      return jsonify({'message': 'No password History'}), 404
    
    if all_history is not None:
      return password_histories_schema.jsonify(all_history), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422

# Getting Password History by name controller (for user)
@token_required 
def password_hist_by_name(user_id,search_name):
  try:
    history = passwordHistService.find_password_history(user_id,search_name)
    if history == []:
      return jsonify({"message": f"No password History for '{search_name}'"}), 404
    
    if history is not None:
      return password_histories_schema.jsonify(history), 201
  except ValueError as e:
    return jsonify({'Error': str(e)}), 422
  