from marshmallow import fields, validate
from schema import ma

class PasswordSchema(ma.Schema):
  password_id = fields.Integer(required=False)
  folder_id = fields.Integer(required=False, allow_none=True)
  user_id = fields.Integer(required=True)
  password_name = fields.String(required=False,validate=validate.Length(min=2))
  username = fields.String(required=False,allow_none=True,validate=validate.Length(min=2))
  email = fields.String(required = True, validate = validate.Email())
  encripted_password = fields.String(required=True, validate=validate.Length(min=12))
  created_date = fields.DateTime(required=False)
  last_updated_date = fields.DateTime(required=False)
  

password_schema = PasswordSchema()
passwords_schema = PasswordSchema(many=True)
