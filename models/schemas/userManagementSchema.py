from marshmallow import fields, validate
from schema import ma

class UserManagementSchema(ma.Schema):
  user_management_role_id = fields.Integer(required=False)
  user_id = fields.Integer(required=True)
  role_id = fields.Integer(required=True)
  
user_management_schema = UserManagementSchema()
users_management_schema = UserManagementSchema(many=True)