from marshmallow import fields, validate
from schema import ma

class PasswordHistorySchema(ma.Schema):
  history_id = fields.Integer(required=False)
  user_id = fields.Integer(required=True)
  password_id = fields.Integer(required=True)
  password_name = fields.String(required=False, validate=validate.Length(min=2))
  email = fields.String(required = True, validate = validate.Email())
  username = fields.String(required=False,validate=validate.Length(min=2))
  old_encripted_password = fields.String(required=True, validate=validate.Length(min=6))
  changed_date = fields.DateTime(required = True)
  
password_history_schema = PasswordHistorySchema()
password_histories_schema = PasswordHistorySchema(many=True)
