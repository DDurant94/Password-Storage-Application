import datetime

from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.passwordHist import PasswordHistory
from services.passwordHistService import (
  save,
  find_passwords_history,
  find_password_history,
  delete,
)
from tests.helpers import BaseFlaskTest, mocked_session


def mock_history_object():
  """Return a mock PasswordHistory object with required schema fields."""
  history = MagicMock(spec=PasswordHistory)
  history.history_id = 1
  history.user_id = 1
  history.action = 'Create'
  history.details = 'created password'
  history.password_id = 10
  history.password_name = 'Github'
  history.username = 'john'
  history.email = 'john@example.com'
  history.old_encripted_password = 'StrongPass123!'
  history.changed_date = datetime.datetime.now()
  return history


class TestPasswordHistoryService(BaseFlaskTest):

  def test_save_history_object(self):
    """Saving history returns a populated PasswordHistory object."""
    password = MagicMock()
    password.user_id = 1
    password.password_id = 99
    password.password_name = 'Github'
    password.username = 'john'
    password.email = 'john@example.com'
    password.encripted_password = 'cipher-text'
    stamp = datetime.datetime.now()

    result = save([password, stamp, 'updated password', 'Update'])

    self.assertEqual(result.user_id, 1)
    self.assertEqual(result.password_id, 99)
    self.assertEqual(result.action, 'Update')
    self.assertEqual(result.details, 'updated password')

  @patch('services.passwordHistService.decrypt')
  @patch('services.passwordHistService.db.session.query')
  @patch('services.passwordHistService.find_user')
  def test_find_passwords_history_success(self, mock_find_user, mock_query, mock_decrypt):
    """Finding all password history decrypts and returns history entries."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    raw_history = [mock_history_object()]
    mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = raw_history
    mock_decrypt.return_value = raw_history

    result = find_passwords_history(1)

    self.assertEqual(result, raw_history)
    mock_decrypt.assert_called_once_with(b'key', raw_history)

  @patch('services.passwordHistService.decrypt')
  @patch('services.passwordHistService.db.session.query')
  @patch('services.passwordHistService.find_user')
  def test_find_password_history_by_name_success(self, mock_find_user, mock_query, mock_decrypt):
    """Finding password history by name decrypts and returns matching entries."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    raw_history = [mock_history_object()]
    mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = raw_history
    mock_decrypt.return_value = raw_history

    result = find_password_history(1, 'Github')

    self.assertEqual(result, raw_history)
    mock_decrypt.assert_called_once_with(b'key', raw_history)

  @patch('services.passwordHistService.Session')
  @patch('services.passwordHistService.find_user')
  def test_delete_success(self, mock_find_user, mock_session):
    """Deleting password history removes all matching records."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    history_items = [MagicMock(), MagicMock()]
    session_instance.execute.return_value.scalars.return_value.all.return_value = history_items

    result = delete(1, {'password_id': 10})

    self.assertEqual(result, 'successful')
    self.assertEqual(session_instance.delete.call_count, 2)

  @patch('services.passwordHistService.Session')
  @patch('services.passwordHistService.find_user')
  def test_delete_no_history(self, mock_find_user, mock_session):
    """Deleting with no history raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.scalars.return_value.all.return_value = []

    with self.assertRaises(ValueError) as context:
      delete(1, {'password_id': 10})

    self.assertIn('No Password History!', str(context.exception))


class TestPasswordHistoryEndpoints(BaseFlaskTest):

  @patch('controllers.passwordHistController.passwordHistService.find_passwords_history')
  def test_get_all_history_success(self, mock_find):
    """GET /history/ returns 201 with password history."""
    mock_find.return_value = [mock_history_object()]

    response = self.client.get('/history/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.passwordHistController.passwordHistService.find_passwords_history')
  def test_get_all_history_accepts_limit_and_offset(self, mock_find):
    """GET /history/ forwards pagination values to the service."""
    mock_find.return_value = [mock_history_object()]

    response = self.client.get('/history/?limit=10&offset=5')

    self.assertEqual(response.status_code, 200)
    self.assertEqual(mock_find.call_args.kwargs['limit'], 10)
    self.assertEqual(mock_find.call_args.kwargs['offset'], 5)

  @patch('controllers.passwordHistController.passwordHistService.find_passwords_history')
  def test_get_all_history_not_found(self, mock_find):
    """GET /history/ returns 404 when user has no history."""
    mock_find.return_value = []

    response = self.client.get('/history/')

    self.assertEqual(response.status_code, 404)
    self.assertIn('No password History', response.get_data(as_text=True))

  @patch('controllers.passwordHistController.passwordHistService.find_passwords_history')
  def test_get_all_history_error(self, mock_find):
    """GET /history/ returns 422 on service error."""
    mock_find.side_effect = ValueError('Something failed')

    response = self.client.get('/history/')

    self.assertEqual(response.status_code, 422)
    self.assertIn('Something failed', response.get_data(as_text=True))

  @patch('controllers.passwordHistController.passwordHistService.find_password_history')
  def test_get_history_by_name_success(self, mock_find):
    """GET /history/search=<name> returns 201 with matching history."""
    mock_find.return_value = [mock_history_object()]

    response = self.client.get('/history/search=Github')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.passwordHistController.passwordHistService.find_password_history')
  def test_get_history_by_name_not_found(self, mock_find):
    """GET /history/search=<name> returns 404 when no matching history exists."""
    mock_find.return_value = []

    response = self.client.get('/history/search=Github')

    self.assertEqual(response.status_code, 404)
    self.assertIn("No password History for 'Github'", response.get_data(as_text=True))


if __name__ == '__main__':
  unittest.main()
