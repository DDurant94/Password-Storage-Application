from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.userSchema import user_schema

from services import userService 


def save():
  try:
    user_data = user_schema.load(request.json)
    
  except ValidationError as err:
    return jsonify(err.messages),400
  try:
    user_save = userService.save(user_data)
    if user_save is not None:
      return user_schema.jsonify(user_save),201
    else:
      return jsonify({"message": "Wait 10 seconds and try again!", "body":user_data}),400
  except ValueError as e:
    return jsonify({"Error": str(e)}),400

@token_required
def find_by_id(user_id):
  try:
    user = userService.find_by_id(int(user_id))
    return user_schema.jsonify(user), 200
  except ValueError as e:
    return jsonify({"Error": str(e)}),400

@token_required
def update(user_id):
  try:
    user_data = user_schema.load(request.json) 
  except ValidationError as err:
    return jsonify(err.messages), 400
  
  try:
    updated_user = userService.update(user_data,user_id)
    
    if updated_user is not None:
      return user_schema.jsonify(updated_user), 201
    
    else:
      return jsonify({"message": "Wait 10 seconds and try again!", "body":"Use a different username."}),400
    
  except ValueError as e:
     return jsonify({"Error": str(e)}),400
   
def login_user():
  user_data = request.json
  
  user = userService.login_user(user_data['username'], user_data['password'])
  
  if user[0]:
    return jsonify(user[0]), 200
  
  else:

    resp = {
      "status": "Error",
      "message": f"Invalid {user[1]}"
    }
      
    return jsonify(resp), 400

@token_required
def delete(user_id):
  user = userService.delete(user_id)
  
  if user == "successful":
    return jsonify({"message": "User removed successfully"}), 200
  else:
    return jsonify({"message": f"Couldn't find User with ID {user_id}"}), 404 