from flask import request, jsonify
from marshmallow import ValidationError

from utils.errorHandlers import ApiError, error_response, invalid_request_body_response, internal_server_error_response, value_error_response
from utils.utils import token_required

from models.schemas.securityQuestionSchema import security_question_schema, security_questions_schema

from services.securityQuestionService import security_question_service, save as security_question_service_save, find as security_question_service_find, update as security_question_service_update, delete as security_question_service_delete


class SecurityQuestionController:
  """Thin HTTP controller that delegates to an injected security-question service."""

  def __init__(self, service=None, schema=None, questions_schema_obj=None):
    self._service = service or security_question_service
    self._schema = schema or security_question_schema
    self._questions_schema = questions_schema_obj or security_questions_schema

  @staticmethod
  def _apply_authenticated_user_id(payload, token_user_id):
    payload['user_id'] = int(token_user_id)
    return payload

  @token_required
  def save(self, user_id):
    try:
      question_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    question_data = self._apply_authenticated_user_id(question_data, user_id)

    try:
      question = self._service.save(user_id, question_data)

      if question is not None:
        return self._schema.jsonify(question), 201
      return jsonify({'message': 'Invalid security question'}), 422

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def find(self, user_id):
    try:
      questions = self._service.find(user_id)
      if questions:
        return self._questions_schema.jsonify(questions), 200

      return error_response("No Security Questions found!", 404)

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def update(self, user_id):
    try:
      question_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    question_data = self._apply_authenticated_user_id(question_data, user_id)

    try:
      new_question = self._service.update(user_id, question_data)
      return self._schema.jsonify(new_question), 201

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()

  @token_required
  def delete(self, user_id):
    try:
      question_data = self._schema.load(request.get_json(silent=True))
    except ValidationError as err:
      return jsonify(err.messages), 400
    except Exception:
      return invalid_request_body_response()

    question_data = self._apply_authenticated_user_id(question_data, user_id)

    try:
      question = self._service.delete(user_id, question_data)

      if question == 'successful':
        return jsonify({'message': "Question removed successfully"}), 200

      return jsonify({'message': 'Question Not Found'}), 404

    except ApiError:
      raise
    except ValueError as e:
      return value_error_response(e)
    except Exception:
      return internal_server_error_response()


security_question_controller = SecurityQuestionController()
securityQuestionService = security_question_service


def save():
  return security_question_controller.save()


def find():
  return security_question_controller.find()


def update():
  return security_question_controller.update()


def delete():
  return security_question_controller.delete()