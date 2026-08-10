from unittest.mock import patch, MagicMock

import unittest

from services.passwordService import save, find_passwords, find_password, update, delete
from tests.helpers import BaseFlaskTest, mocked_session
from tests.password.test_data import mock_password_data, mock_password_object


class TestPasswordService(BaseFlaskTest):

  @patch('services.passwordService.hist_func')
  @patch('services.passwordService.encrypted')
  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_encrypted, mock_hist_func):
    user = MagicMock()
    user.user_id = 1
    user.username = 'john'
    mock_find_user.return_value = [user, b'key']
    mock_encrypted.return_value = 'cipher'
    mock_hist_func.return_value = MagicMock()

    session_instance = mocked_session(mock_session)
    result = save(1, mock_password_data())

    self.assertIsNotNone(result)
    self.assertEqual(result.password_name, 'Github')
    self.assertEqual(result.encripted_password, 'cipher')
    self.assertGreaterEqual(session_instance.add.call_count, 2)

  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_save_folder_not_found(self, mock_session, mock_find_user):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None
    payload = mock_password_data()
    payload['folder_id'] = 999

    with self.assertRaises(ValueError) as context:
      save(1, payload)

    self.assertIn('Folder not found!', str(context.exception))

  @patch('services.passwordService.decrypted')
  @patch('services.passwordService.db.session.query')
  @patch('services.passwordService.find_user')
  def test_find_passwords_success(self, mock_find_user, mock_query, mock_decrypted):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    pwd = mock_password_object()
    pwd.encripted_password = 'cipher'
    mock_query.return_value.filter.return_value.all.return_value = [pwd]
    mock_decrypted.return_value = 'StrongPass123!'

    result = find_passwords(1)

    self.assertEqual(len(result), 1)
    self.assertEqual(result[0].encripted_password, 'StrongPass123!')

  @patch('services.passwordService.db.session.query')
  @patch('services.passwordService.find_user')
  def test_find_password_not_found(self, mock_find_user, mock_query):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_query.return_value.filter.return_value.one_or_none.return_value = None

    result = find_password(1, 'Nope')

    self.assertIsNone(result)

  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_update_invalid_password(self, mock_session, mock_find_user):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    with self.assertRaises(ValueError) as context:
      update(1, mock_password_data())

    self.assertIn('Invalid Password!', str(context.exception))

  @patch('services.passwordService.hist_delete')
  def test_delete_invalid_user(self, mock_hist_delete):
    mock_hist_delete.return_value = 'successful'
    payload = mock_password_data()
    payload['user_id'] = 2

    with self.assertRaises(ValueError) as context:
      delete(1, payload)

    self.assertIn('Invalid User', str(context.exception))

  @patch('services.passwordService.hist_delete')
  @patch('services.passwordService.Session')
  def test_delete_success(self, mock_session, mock_hist_delete):
    mock_hist_delete.return_value = 'successful'
    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_password_object()

    result = delete(1, mock_password_data())

    self.assertEqual(result, 'successful')
    session_instance.delete.assert_called_once()


if __name__ == '__main__':
  unittest.main()
