from marshmallow import fields, validate
from schema import ma

class AuditLogSchema(ma.Schema):
  audit_id = fields.Integer(required=False)
  user_id = fields.Integer(required=True)
  action = fields.String(required=True, validate=validate.Length(min=3))
  details = fields.String(required=False, validate=validate.Length(min=3))
  ip_address = fields.String(required=True)
   
audit_log_schema = AuditLogSchema()
audit_logs_schema =AuditLogSchema(many=True)