from marshmallow import fields, validate
from schema import ma

class FolderSchema(ma.Schema):
  folder_id = fields.Integer(required=False)
  user_id = fields.Integer(required=True)
  parent_folder_id = fields.Integer(required=False, allow_none = True)
  folder_name = fields.String(required=False, validate=validate.Length(min=2))
  created_date = fields.DateTime(required = False)
  
folder_schema = FolderSchema()
folders_schema = FolderSchema(many=True)