from marshmallow import fields, validate
from schema import ma

class UserSchema(ma.Schema):
  user_id = fields.Integer(required = False)
  username = fields.String(required = True, validate = validate.Length(min=6,max=12))
  password = fields.String(required = True, validate = validate.Length(min=8,max=20))
  first_name = fields.String(required = True, validate = validate.Length(min=2,max=30))
  last_name = fields.String(required = True, validate = validate.Length(min=2,max=30))
  email = fields.String(required = True, validate = validate.Email())
  create_date = fields.DateTime(required = False)
  updated_date = fields.DateTime(required = False)
  role = fields.String(required=False,validate=validate.Length(min=2))
  
  
user_schema = UserSchema()
users_schema = UserSchema(many=True)
