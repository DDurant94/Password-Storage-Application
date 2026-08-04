import datetime

from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.auditLog import AuditLog
from services.auditLogService import save, find
from tests.helpers import BaseFlaskTest, mocked_session


def mock_audit_log_object():
  """Return a mock AuditLog object with required schema fields."""
  log = MagicMock(spec=AuditLog)
  log.audit_id = 1
  log.user_id = 1
  log.action = 'Login'
  log.details = 'user login'
  log.ip_address = '127.0.0.1'
  log.time_stamp = datetime.datetime.now()
  return log


class TestAuditLogService(BaseFlaskTest):

  @patch('services.auditLogService.encrypted')
  @patch('services.auditLogService.make_key')
  @patch('services.auditLogService.time')
  def test_save_success(self, mock_time, mock_make_key, mock_encrypted):
    """Saving an audit log returns a populated AuditLog object."""
    stamp = datetime.datetime.now()
    mock_time.return_value = stamp
    mock_make_key.return_value = b'key'
    mock_encrypted.return_value = 'cipher-ip'
    user = MagicMock()
    user.user_id = 1
    user.key = b'k'
    user.password = 'hash'

    with self.app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
      result = save(user, 'Login', 'User logged in')

    self.assertEqual(result.user_id, 1)
    self.assertEqual(result.action, 'Login')
    self.assertEqual(result.details, 'User logged in')
    self.assertEqual(result.ip_address, 'cipher-ip')

  @patch('services.auditLogService.decrypted')
  @patch('services.auditLogService.db.session.query')
  @patch('services.auditLogService.find_user')
  def test_find_success(self, mock_find_user, mock_query, mock_decrypted):
    """Finding audit logs decrypts IP addresses before returning."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    log_1 = mock_audit_log_object()
    log_1.ip_address = 'enc-1'
    log_2 = mock_audit_log_object()
    log_2.ip_address = 'enc-2'

    mock_query.return_value.filter.return_value.all.return_value = [log_1, log_2]
    mock_decrypted.side_effect = ['127.0.0.1', '10.0.0.1']

    result = find(1)

    self.assertEqual(len(result), 2)
    self.assertEqual(result[0].ip_address, '127.0.0.1')
    self.assertEqual(result[1].ip_address, '10.0.0.1')
    self.assertEqual(mock_decrypted.call_count, 2)

  @patch('services.auditLogService.encrypted')
  @patch('services.auditLogService.decrypted')
  @patch('services.auditLogService.Session')
  def test_finder_rekeys_audits(self, mock_session, mock_decrypted, mock_encrypted):
    """Finder re-encrypts existing audit log IP addresses with the new key."""
    session_instance = mocked_session(mock_session)
    log = mock_audit_log_object()
    log.ip_address = 'old-cipher'
    session_instance.execute.return_value.scalars.return_value.all.return_value = [log]

    user = MagicMock()
    user.user_id = 1
    mock_decrypted.return_value = '127.0.0.1'
    mock_encrypted.return_value = 'new-cipher'

    from services.auditLogService import finder
    result = finder(b'old-key', user, b'new-key')

    self.assertEqual(result[0].ip_address, 'new-cipher')
    session_instance.commit.assert_called_once()


class TestAuditLogEndpoints(BaseFlaskTest):

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_success(self, mock_find):
    """GET /audit/ returns 200 with audit log records."""
    mock_find.return_value = [mock_audit_log_object()]

    response = self.client.get('/audit/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_error(self, mock_find):
    """GET /audit/ returns 422 when service raises ValueError."""
    mock_find.side_effect = ValueError('Unable to fetch logs')

    response = self.client.get('/audit/')

    self.assertEqual(response.status_code, 422)
    self.assertIn('Unable to fetch logs', response.get_data(as_text=True))


if __name__ == '__main__':
  unittest.main()
