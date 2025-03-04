from marshmallow import fields, validate
from schema import ma

class SecurityQuestionSchema(ma.Schema):
  question_id = fields.Integer(required=False)
  user_id = fields.Integer(required=True)
  question = fields.String(required=True, validate = validate.Length(min=5))
  encripted_answer = fields.String(required=True, validate=validate.Length(min=2))
  
security_question_schema = SecurityQuestionSchema()
security_questions_schema = SecurityQuestionSchema(many=True)
