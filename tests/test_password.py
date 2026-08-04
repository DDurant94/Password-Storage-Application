import datetime

from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.passwords import Password
from services.passwordService import save, find_passwords, find_password, update, delete
from tests.helpers import BaseFlaskTest, mocked_session


def mock_password_data():
  """Return valid password request payload data."""
  return {
    'password_id': 1,
    'folder_id': None,
    'user_id': 1,
    'password_name': 'Github',
    'username': 'john',
    'email': 'john@example.com',
    'encripted_password': 'StrongPass123!'
  }


def mock_password_object():
  """Return a mock Password object with required schema fields."""
  pwd = MagicMock(spec=Password)
  pwd.password_id = 1
  pwd.folder_id = None
  pwd.user_id = 1
  pwd.password_name = 'Github'
  pwd.username = 'john'
  pwd.email = 'john@example.com'
  pwd.encripted_password = 'StrongPass123!'
  pwd.created_date = datetime.datetime.now()
  pwd.last_updated_date = datetime.datetime.now()
  return pwd


class TestPasswordService(BaseFlaskTest):

  @patch('services.passwordService.hist_func')
  @patch('services.passwordService.encrypted')
  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_encrypted, mock_hist_func):
    """Saving password stores encrypted password and history record."""
    user = MagicMock()
    user.user_id = 1
    user.username = 'john'
    mock_find_user.return_value = [user, b'key']
    mock_encrypted.return_value = 'cipher'
    mock_hist_func.return_value = MagicMock()

    session_instance = mocked_session(mock_session)
    payload = mock_password_data()

    result = save(1, payload)

    self.assertIsNotNone(result)
    self.assertEqual(result.password_name, 'Github')
    self.assertEqual(result.encripted_password, 'cipher')
    self.assertGreaterEqual(session_instance.add.call_count, 2)

  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_save_folder_not_found(self, mock_session, mock_find_user):
    """Saving password with invalid folder_id raises ValueError."""
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
    """Finding all passwords decrypts each password value."""
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
    """Finding one password returns None when no match exists."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_query.return_value.filter.return_value.one_or_none.return_value = None

    result = find_password(1, 'Nope')

    self.assertIsNone(result)

  @patch('services.passwordService.find_user')
  @patch('services.passwordService.Session')
  def test_update_invalid_password(self, mock_session, mock_find_user):
    """Updating a non-existent password raises ValueError."""
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
    """Deleting password with mismatched user_id raises ValueError."""
    mock_hist_delete.return_value = 'successful'
    payload = mock_password_data()
    payload['user_id'] = 2

    with self.assertRaises(ValueError) as context:
      delete(1, payload)

    self.assertIn('Invalid User', str(context.exception))

  @patch('services.passwordService.hist_delete')
  @patch('services.passwordService.Session')
  def test_delete_success(self, mock_session, mock_hist_delete):
    """Deleting password removes the record when history deletion succeeds."""
    mock_hist_delete.return_value = 'successful'
    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_password_object()

    result = delete(1, mock_password_data())

    self.assertEqual(result, 'successful')
    session_instance.delete.assert_called_once()


class TestPasswordEndpoints(BaseFlaskTest):

  @patch('controllers.passwordController.passwordService.save')
  def test_post_password_success(self, mock_save):
    """POST /password/ returns 201 on successful create."""
    mock_save.return_value = mock_password_object()

    response = self.client.post(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_password_validation_error(self):
    """POST /password/ returns 400 for invalid payload."""
    response = self.client.post('/password/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.passwordController.passwordService.find_passwords')
  def test_get_passwords_success(self, mock_find):
    """GET /password/ returns 201 with all passwords."""
    mock_find.return_value = [mock_password_object()]

    response = self.client.get('/password/')

    self.assertEqual(response.status_code, 201)

  @patch('controllers.passwordController.passwordService.find_password')
  def test_get_password_by_name_not_found(self, mock_find):
    """GET /password/search=<name> returns 404 when not found."""
    mock_find.return_value = None

    response = self.client.get('/password/search=Nope')

    self.assertEqual(response.status_code, 404)
    self.assertIn("Couldn't find 'Nope'", response.get_data(as_text=True))

  @patch('controllers.passwordController.passwordService.find_password')
  def test_get_password_by_name_success(self, mock_find):
    """GET /password/search=<name> returns 201 for a match."""
    mock_find.return_value = mock_password_object()

    response = self.client.get('/password/search=Github')

    self.assertEqual(response.status_code, 201)

  @patch('controllers.passwordController.passwordService.update')
  def test_put_password_success(self, mock_update):
    """PUT /password/ returns 201 on successful update."""
    mock_update.return_value = mock_password_object()

    response = self.client.put(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.passwordController.passwordService.update')
  def test_put_password_error(self, mock_update):
    """PUT /password/ returns 422 on service error."""
    mock_update.side_effect = ValueError('Invalid Password!')

    response = self.client.put(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Invalid Password!', response.get_data(as_text=True))

  @patch('controllers.passwordController.passwordService.delete')
  def test_delete_password_success(self, mock_delete):
    """DELETE /password/ returns 200 when delete succeeds."""
    mock_delete.return_value = 'successful'

    response = self.client.delete(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn('Password has be removed!', response.get_data(as_text=True))

  @patch('controllers.passwordController.passwordService.delete')
  def test_delete_password_not_found(self, mock_delete):
    """DELETE /password/ returns 404 when password is missing."""
    mock_delete.return_value = None

    response = self.client.delete(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
