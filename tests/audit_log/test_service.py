import datetime

from unittest.mock import patch, MagicMock

import unittest

from services.auditLogService import save, find
from tests.audit_log.test_data import mock_audit_log_object
from tests.helpers import BaseFlaskTest, mocked_session


class TestAuditLogService(BaseFlaskTest):

  @patch('services.auditLogService.encrypted')
  @patch('services.auditLogService.make_key')
  @patch('services.auditLogService.time')
  def test_save_success(self, mock_time, mock_make_key, mock_encrypted):
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


if __name__ == '__main__':
  unittest.main()
