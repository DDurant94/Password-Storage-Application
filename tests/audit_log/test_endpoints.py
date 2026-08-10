from unittest.mock import patch

import unittest

from tests.audit_log.test_data import mock_audit_log_object
from tests.helpers import BaseFlaskTest
from utils.error_handlers import ApiError


class TestAuditLogEndpoints(BaseFlaskTest):

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_success(self, mock_find):
    mock_find.return_value = [mock_audit_log_object()]

    response = self.client.get('/audit/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_accepts_limit_and_offset(self, mock_find):
    mock_find.return_value = [mock_audit_log_object()]

    response = self.client.get('/audit/?limit=10&offset=5')

    self.assertEqual(response.status_code, 200)
    self.assertEqual(mock_find.call_args.kwargs['limit'], 10)
    self.assertEqual(mock_find.call_args.kwargs['offset'], 5)

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_error(self, mock_find):
    mock_find.side_effect = ValueError('Unable to fetch logs')

    response = self.client.get('/audit/')

    self.assertEqual(response.status_code, 422)
    self.assertIn('Unable to fetch logs', response.get_data(as_text=True))

  @patch('controllers.auditLogController.auditLogService.find')
  def test_get_audit_logs_service_unavailable(self, mock_find):
    mock_find.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.get('/audit/')

    self.assertEqual(response.status_code, 503)
    self.assertIn('Service temporarily unavailable', response.get_data(as_text=True))


if __name__ == '__main__':
  unittest.main()
