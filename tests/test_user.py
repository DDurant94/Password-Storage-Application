"""
Unit and endpoint tests for the User service and API endpoints.

- Service layer tests mock the DB/session and test business logic.
- Endpoint tests use Flask's test client and patch authentication decorators.
- All authentication decorators are patched at the top to bypass auth in tests.
- Shared setup/teardown via BaseFlaskTest.
"""

import datetime

from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.role import Role
from models.user import User
from services.userService import save, find_by_id, update, login_user, delete
from tests.helpers import BaseFlaskTest, mocked_session

# --- Helper Data Factories ---

def mock_user_input():
  """Return valid user registration data."""
  return {
    "username": "testuser",
    "password": "TestPassword1!",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }

def mock_user_update_input():
  """Return valid user update data with different field values."""
  return {
    "username": "testuser",
    "password": "TestPassword1!",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com"
  }

def mock_user_object():
  """Return a mock User object with all required attributes set."""
  mock_user = MagicMock(spec=User)
  mock_user.user_id = 1
  mock_user.username = "testuser"
  mock_user.password = "hashed_password"
  mock_user.first_name = "John"
  mock_user.last_name = "Doe"
  mock_user.email = "john.doe@example.com"
  mock_user.role = "user"
  mock_user.roles = []
  mock_user.key = b'\x00' * 16
  mock_user.create_date = datetime.datetime.now()
  mock_user.updated_date = datetime.datetime.now()
  return mock_user

def mock_role_object():
  """Return a mock Role object."""
  mock_role = MagicMock(spec=Role)
  mock_role.role_id = 1
  mock_role.role_name = "user"
  return mock_role

# --- Shared Base Test Class ---

# --- Service Layer Tests ---

class TestUserService(BaseFlaskTest):

  @patch('services.userService.audit_log')
  @patch('services.userService.db.session.execute')
  @patch('services.userService.Session')
  def test_save_success(self, mock_session, mock_db_execute, mock_audit_log):
    """Saving a new user successfully creates and returns a User."""
    user_data = mock_user_input()
    mock_role = mock_role_object()

    # First call: check if user exists → None (doesn't exist yet)
    no_user_result = MagicMock()
    no_user_result.unique.return_value.scalar_one_or_none.return_value = None
    # Second call: look up the role → role found
    role_result = MagicMock()
    role_result.scalar_one_or_none.return_value = mock_role
    mock_db_execute.side_effect = [no_user_result, role_result]

    mock_audit_log.return_value = MagicMock()

    result = save(user_data)

    self.assertIsNotNone(result)
    self.assertEqual(result.username, user_data['username'])
    self.assertEqual(result.first_name, user_data['first_name'])
    self.assertEqual(result.last_name, user_data['last_name'])
    self.assertEqual(result.email, user_data['email'])
    self.assertEqual(mock_db_execute.call_count, 2)

  @patch('services.userService.db.session.execute')
  @patch('services.userService.Session')
  def test_save_user_already_exists(self, mock_session, mock_db_execute):
    """Saving a duplicate user raises ValueError."""
    existing_user = mock_user_object()
    result = MagicMock()
    result.unique.return_value.scalar_one_or_none.return_value = existing_user
    mock_db_execute.return_value = result

    with self.assertRaises(ValueError) as ctx:
      save(mock_user_input())

    self.assertIn("User Already Exists!", str(ctx.exception))

  @patch('services.userService.audit_log')
  @patch('services.userService.db.session.execute')
  @patch('services.userService.Session')
  def test_save_role_not_found(self, mock_session, mock_db_execute, mock_audit_log):
    """Saving a user with a non-existent role raises ValueError."""
    user_data = {**mock_user_input(), "role": "nonexistent_role"}

    no_user_result = MagicMock()
    no_user_result.unique.return_value.scalar_one_or_none.return_value = None
    no_role_result = MagicMock()
    no_role_result.scalar_one_or_none.return_value = None  # role not found
    mock_db_execute.side_effect = [no_user_result, no_role_result]

    with self.assertRaises(ValueError) as ctx:
      save(user_data)

    self.assertIn("Role Not Found!", str(ctx.exception))

  @patch('services.userService.find_user')
  def test_find_by_id_success(self, mock_find_user):
    """Finding a user by ID returns the correct User object."""
    mock_user = mock_user_object()
    mock_find_user.return_value = [mock_user, b'somekey']

    result = find_by_id(1)

    self.assertEqual(result, mock_user)
    mock_find_user.assert_called_once_with(1)

  @patch('services.userService.find_user')
  def test_find_by_id_not_found(self, mock_find_user):
    """Finding a non-existent user raises ValueError from the utility."""
    mock_find_user.side_effect = ValueError("User not found!")

    with self.assertRaises(ValueError) as ctx:
      find_by_id(999)

    self.assertIn("User not found!", str(ctx.exception))

  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_update_success(self, mock_session, mock_check_hash, mock_audit_log):
    """Updating a user's details commits changes and returns the user."""
    user_data = mock_user_update_input()
    mock_user = mock_user_object()
    mock_audit_log.return_value = MagicMock()

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_user
    mock_check_hash.return_value = True  # password is unchanged

    result = update(user_data, 1)

    self.assertIsNotNone(result)
    self.assertEqual(mock_user.first_name, user_data['first_name'])
    self.assertEqual(mock_user.last_name, user_data['last_name'])
    self.assertEqual(mock_user.email, user_data['email'])
    mock_session_instance.commit.assert_called_once()
    mock_session_instance.refresh.assert_called_once()

  @patch('services.userService.Session')
  def test_update_user_not_found(self, mock_session):
    """Updating a non-existent user raises ValueError."""
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    with self.assertRaises(ValueError) as ctx:
      update(mock_user_update_input(), 999)

    self.assertIn("User not Found!", str(ctx.exception))
    mock_session_instance.commit.assert_not_called()

  @patch('services.userService.update_getter')
  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_update_password_triggers_rekey(self, mock_session, mock_check_hash, mock_audit_log, mock_update_getter):
    """Changing the password during update triggers the rekeying of encrypted data."""
    user_data = mock_user_update_input()
    mock_user = mock_user_object()
    mock_audit_log.return_value = MagicMock()
    mock_update_getter.return_value = [[], [], [], []]

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_user
    mock_check_hash.return_value = False  # password has changed

    result = update(user_data, 1)

    self.assertIsNotNone(result)
    mock_update_getter.assert_called_once()
    mock_session_instance.commit.assert_called_once()

  @patch('services.userService.encode_token')
  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_login_success(self, mock_session, mock_check_hash, mock_audit_log, mock_encode):
    """Logging in with correct credentials returns a success response with an auth token."""
    mock_user = mock_user_object()
    mock_role = mock_role_object()
    mock_user.roles = [mock_role]
    mock_check_hash.return_value = True
    mock_encode.return_value = "fake.jwt.token"
    mock_audit_log.return_value = MagicMock()

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_user

    result = login_user("testuser", "TestPassword1!")

    self.assertIsNotNone(result[0])
    self.assertEqual(result[0]['status'], 'success')
    self.assertEqual(result[0]['auth_token'], "fake.jwt.token")
    self.assertEqual(result[1], 'success')

  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_login_wrong_password(self, mock_session, mock_check_hash, mock_audit_log):
    """Logging in with an incorrect password returns a password failure indicator."""
    mock_user = mock_user_object()
    mock_check_hash.return_value = False
    mock_audit_log.return_value = MagicMock()

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_user

    result = login_user("testuser", "WrongPassword!")

    self.assertIsNone(result[0])
    self.assertEqual(result[1], 'Password')

  @patch('services.userService.Session')
  def test_login_wrong_username(self, mock_session):
    """Logging in with an unknown username returns a username failure indicator."""
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    result = login_user("unknownuser", "TestPassword1!")

    self.assertIsNone(result[0])
    self.assertEqual(result[1], 'Username')

  @patch('services.userService.db.session.execute')
  @patch('services.userService.Session')
  def test_delete_success(self, mock_session, mock_db_execute):
    """Deleting an existing user removes it and returns 'successful'."""
    mock_user = mock_user_object()
    user_result = MagicMock()
    user_result.unique.return_value.scalar_one_or_none.return_value = mock_user
    mock_db_execute.return_value = user_result

    mock_session_instance = mocked_session(mock_session)

    result = delete(1)

    self.assertEqual(result, "successful")
    mock_session_instance.delete.assert_called_once_with(mock_user)

  @patch('services.userService.db.session.execute')
  @patch('services.userService.Session')
  def test_delete_user_not_found(self, mock_session, mock_db_execute):
    """Deleting a non-existent user returns None."""
    no_user_result = MagicMock()
    no_user_result.unique.return_value.scalar_one_or_none.return_value = None
    mock_db_execute.return_value = no_user_result

    result = delete(999)

    self.assertIsNone(result)

# --- Endpoint Tests ---

class TestUserEndpoints(BaseFlaskTest):
  """Endpoint tests for /user/ API endpoints."""

  @patch('controllers.userController.userService.save')
  def test_post_user_success(self, mock_save):
    """POST /user/ returns 201 when user is created successfully."""
    mock_save.return_value = mock_user_object()

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.userController.userService.save')
  def test_post_user_already_exists(self, mock_save):
    """POST /user/ returns 422 if the user already exists."""
    mock_save.side_effect = ValueError("User Already Exists!")

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn("User Already Exists!", response.get_data(as_text=True))

  def test_post_user_validation_error(self):
    """POST /user/ returns 400 when required fields are missing or invalid."""
    response = self.client.post(
      '/user/',
      data=json.dumps({"username": "usr"}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.save')
  def test_post_user_circuit_breaker_fallback(self, mock_save):
    """POST /user/ returns 400 with a retry message when the circuit breaker is open."""
    mock_save.return_value = None  # simulate circuit open / fallback

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertIn("Wait 10 seconds", response.get_data(as_text=True))

  @patch('controllers.userController.userService.find_by_id')
  def test_get_user_success(self, mock_find):
    """GET /user/ returns 200 with the user's data."""
    mock_find.return_value = mock_user_object()

    response = self.client.get('/user/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.userController.userService.find_by_id')
  def test_get_user_not_found(self, mock_find):
    """GET /user/ returns 422 when the user does not exist."""
    mock_find.side_effect = ValueError("User not found!")

    response = self.client.get('/user/')

    self.assertEqual(response.status_code, 422)
    self.assertIn("User not found!", response.get_data(as_text=True))

  @patch('controllers.userController.userService.update')
  def test_put_user_success(self, mock_update):
    """PUT /user/ returns 201 with updated user data."""
    mock_update.return_value = mock_user_object()

    response = self.client.put(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.userController.userService.update')
  def test_put_user_not_found(self, mock_update):
    """PUT /user/ returns 422 when the user to update does not exist."""
    mock_update.side_effect = ValueError("User not Found!")

    response = self.client.put(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn("User not Found!", response.get_data(as_text=True))

  def test_put_user_validation_error(self):
    """PUT /user/ returns 400 when required fields are missing or invalid."""
    response = self.client.put(
      '/user/',
      data=json.dumps({"username": "usr"}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.login_user')
  def test_post_login_success(self, mock_login):
    """POST /user/login returns 200 with an auth token on successful login."""
    mock_login.return_value = [
      {"status": "success", "message": "Successfully logged in", "auth_token": "fake.jwt.token"},
      "success"
    ]

    response = self.client.post(
      '/user/login',
      data=json.dumps({"username": "testuser", "password": "TestPassword1!"}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    data = json.loads(response.data)
    self.assertEqual(data['status'], 'success')
    self.assertIn('auth_token', data)

  @patch('controllers.userController.userService.login_user')
  def test_post_login_invalid_password(self, mock_login):
    """POST /user/login returns 422 with an error message for a wrong password."""
    mock_login.return_value = [None, "Password"]

    response = self.client.post(
      '/user/login',
      data=json.dumps({"username": "testuser", "password": "WrongPass123!"}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    data = json.loads(response.data)
    self.assertEqual(data['message'], 'Invalid Password')

  @patch('controllers.userController.userService.login_user')
  def test_post_login_invalid_username(self, mock_login):
    """POST /user/login returns 422 with an error message for an unknown username."""
    mock_login.return_value = [None, "Username"]

    response = self.client.post(
      '/user/login',
      data=json.dumps({"username": "noexist", "password": "TestPassword1!"}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    data = json.loads(response.data)
    self.assertEqual(data['message'], 'Invalid Username')

  @patch('controllers.userController.userService.delete')
  def test_delete_user_success(self, mock_delete):
    """DELETE /user/ returns 200 when the user is removed successfully."""
    mock_delete.return_value = "successful"

    response = self.client.delete('/user/')

    self.assertEqual(response.status_code, 200)
    self.assertIn("User removed successfully", response.get_data(as_text=True))

  @patch('controllers.userController.userService.delete')
  def test_delete_user_not_found(self, mock_delete):
    """DELETE /user/ returns 404 when the user does not exist."""
    mock_delete.return_value = None

    response = self.client.delete('/user/')

    self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
  unittest.main()