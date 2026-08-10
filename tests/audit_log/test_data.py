import datetime
from unittest.mock import MagicMock

from models.auditLog import AuditLog


def mock_audit_log_object():
  log = MagicMock(spec=AuditLog)
  log.audit_id = 1
  log.user_id = 1
  log.action = 'Login'
  log.details = 'user login'
  log.ip_address = '127.0.0.1'
  log.time_stamp = datetime.datetime.now()
  return log
