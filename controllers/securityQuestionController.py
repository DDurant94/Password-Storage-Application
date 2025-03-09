from flask import request, jsonify
from marshmallow import ValidationError
from caching import cache

from utils.util import token_required, role_required

from models.schemas.securityQuestionSchema import security_question_schema, security_questions_schema

from services import securityQuestionService

@token_required
def save(user_id):
  try:
    question_data = security_question_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    question = securityQuestionService.save(user_id,question_data)
    
    if question is not None:
      return security_question_schema.jsonify(question), 201
    else:
      return jsonify({'message': 'Invalid security question'}), 422
  
  except ValueError as e:
    return jsonify({"Error": str(e)}),422
  
@token_required
def find(user_id):
  try:
    questions = securityQuestionService.find(user_id)
    if questions:
      return security_questions_schema.jsonify(questions), 200
    
    else:
      return jsonify({"message": "No Security Questions found!"}), 404
    
  except ValueError as e:
    return jsonify({"Error": str(e)}),422
  
@token_required
def update(user_id):
  try:
    question_data = security_question_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    new_question = securityQuestionService.update(user_id,question_data)
    
    return security_question_schema.jsonify(new_question),201
    
  except ValueError as e:
    return jsonify({"Error": str(e)}),422
  
@token_required
def delete(user_id):
  try:
    question_data = security_question_schema.load(request.json)
  except ValidationError as err:
    return jsonify(err.messages),400
  
  try:
    question = securityQuestionService.delete(user_id, question_data)
    
    if question == 'successful':
      return jsonify({'message': "Question removed successfully"}), 200
    
    else:
      return jsonify({'message': 'Question Not Found'}), 404
    
  except ValueError as e:
    return jsonify({"Error": str(e)}),422