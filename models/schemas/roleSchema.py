from marshmallow import fields, validate
from schema import ma

class RoleSchema(ma.Schema):
  role_id = fields.Integer(required=False)
  role_name = fields.String(required=True, validate = validate.Length(min=2))
  
role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)
