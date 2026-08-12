import datetime
import unittest

from unittest.mock import MagicMock, patch

from services.userService import UserService
from tests.helpers import BaseFlaskTest, mocked_session
from tests.user.test_data import (
  mock_role_object,
  mock_user_input,
  mock_user_object,
  mock_user_update_input,
  role_lookup_result,
  token_list_result,
  token_lookup_result,
  user_lookup_result,
)
from utils.errorHandlers import ApiError


class TestUserService(BaseFlaskTest):

  @patch('services.userService.audit_log')
  @patch('services.userService.Session')
  def test_save_success(self, mock_session, mock_audit_log):
    user_data = mock_user_input()
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.side_effect = [
      user_lookup_result(None),
      role_lookup_result(mock_role_object()),
    ]
    mock_audit_log.return_value = MagicMock()

    service = UserService()
    result = service.save(user_data)

    self.assertIsNotNone(result)
    self.assertEqual(result.username, user_data['username'])
    self.assertEqual(mock_session_instance.execute.call_count, 2)

  @patch('services.userService.Session')
  def test_save_user_already_exists(self, mock_session):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value = user_lookup_result(mock_user_object())

    service = UserService()
    with self.assertRaises(ValueError) as ctx:
      service.save(mock_user_input())

    self.assertIn('User Already Exists!', str(ctx.exception))

  @patch('services.userService.audit_log')
  @patch('services.userService.Session')
  def test_save_role_not_found(self, mock_session, mock_audit_log):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.side_effect = [
      user_lookup_result(None),
      role_lookup_result(None),
    ]
    mock_audit_log.return_value = MagicMock()

    service = UserService()
    with self.assertRaises(ValueError) as ctx:
      service.save({**mock_user_input(), 'role': 'missing'})

    self.assertIn('Role Not Found!', str(ctx.exception))

  @patch('services.userService.find_user')
  def test_find_by_id_success(self, mock_find_user):
    expected = mock_user_object()
    mock_find_user.return_value = [expected, b'key']

    service = UserService()
    result = service.find_by_id(1)

    self.assertEqual(result, expected)

  @patch('services.userService.find_user')
  def test_find_by_id_not_found(self, mock_find_user):
    mock_find_user.side_effect = ValueError('User not found!')

    service = UserService()
    with self.assertRaises(ValueError):
      service.find_by_id(999)

  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_update_success(self, mock_session, mock_check_hash, mock_audit_log):
    mock_session_instance = mocked_session(mock_session)
    mock_user = mock_user_object()
    mock_session_instance.execute.return_value = user_lookup_result(mock_user)
    mock_check_hash.return_value = True
    mock_audit_log.return_value = MagicMock()

    service = UserService()
    result = service.update(mock_user_update_input(), 1)

    self.assertIsNotNone(result)
    self.assertEqual(mock_user.first_name, 'Jane')
    self.assertEqual(mock_user.last_name, 'Smith')
    self.assertEqual(mock_user.email, 'jane.smith@example.com')
    mock_session_instance.refresh.assert_called_once()

  @patch('services.userService.Session')
  def test_update_user_not_found(self, mock_session):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value = user_lookup_result(None)

    service = UserService()
    with self.assertRaises(ValueError) as ctx:
      service.update(mock_user_update_input(), 999)

    self.assertIn('User not Found!', str(ctx.exception))

  @patch('services.userService.update_getter')
  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_update_password_triggers_rekey(self, mock_session, mock_check_hash, mock_audit_log, mock_update_getter):
    mock_session_instance = mocked_session(mock_session)
    mock_user = mock_user_object()
    mock_session_instance.execute.return_value = user_lookup_result(mock_user)
    mock_check_hash.return_value = False
    mock_audit_log.return_value = MagicMock()
    mock_update_getter.return_value = [[], [], [], []]

    service = UserService()
    result = service.update(mock_user_update_input(), 1)

    self.assertIsNotNone(result)
    mock_update_getter.assert_called_once()

  @patch('services.userService.update_getter')
  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_update_password_rekeys_before_password_change(self, mock_session, mock_check_hash, mock_audit_log, mock_update_getter):
    mock_session_instance = mocked_session(mock_session)
    mock_user = mock_user_object()
    mock_session_instance.execute.return_value = user_lookup_result(mock_user)
    mock_check_hash.return_value = False
    mock_audit_log.return_value = MagicMock()
    mock_update_getter.return_value = [[], [], [], []]
    original_password = mock_user.password

    service = UserService()
    updated_user = service.update(mock_user_update_input(), 1)

    self.assertIsNotNone(updated_user)
    self.assertNotEqual(updated_user.password, original_password)
    mock_update_getter.assert_called_once_with(mock_user, updated_user.password)

  @patch('services.userService.decode_refresh_token')
  @patch('services.userService.encode_refresh_token')
  @patch('services.userService.encode_token')
  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_login_success(self, mock_session, mock_check_hash, mock_audit_log, mock_encode, mock_encode_refresh, mock_decode_refresh):
    mock_session_instance = mocked_session(mock_session)
    mock_user = mock_user_object()
    mock_user.roles = [mock_role_object()]
    mock_session_instance.execute.return_value = user_lookup_result(mock_user)

    mock_check_hash.return_value = True
    mock_audit_log.return_value = MagicMock()
    mock_encode.return_value = 'fake.jwt.token'
    mock_encode_refresh.return_value = 'fake.refresh.token'
    mock_decode_refresh.return_value = {
      'jti': 'login-jti',
      'exp': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).timestamp(),
      'sub': '1',
    }

    service = UserService()
    result = service.login_user('testuser', 'TestPassword1!')

    self.assertEqual(result[1], 'success')
    self.assertEqual(result[0]['auth_token'], 'fake.jwt.token')
    self.assertEqual(result[0]['refresh_token'], 'fake.refresh.token')

  @patch('services.userService.audit_log')
  @patch('services.userService.check_password_hash')
  @patch('services.userService.Session')
  def test_login_wrong_password(self, mock_session, mock_check_hash, mock_audit_log):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value = user_lookup_result(mock_user_object())
    mock_check_hash.return_value = False
    mock_audit_log.return_value = MagicMock()

    service = UserService()
    result = service.login_user('testuser', 'wrong')

    self.assertIsNone(result[0])
    self.assertEqual(result[1], 'Password')

  @patch('services.userService.Session')
  def test_login_wrong_username(self, mock_session):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value = user_lookup_result(None)

    service = UserService()
    result = service.login_user('missing', 'whatever')

    self.assertIsNone(result[0])
    self.assertEqual(result[1], 'Username')

  @patch('services.userService.decode_refresh_token')
  @patch('services.userService.encode_refresh_token')
  @patch('services.userService.encode_token')
  @patch('services.userService.Session')
  def test_refresh_token_rotation_success(self, mock_session, mock_encode, mock_encode_refresh, mock_decode_refresh):
    mock_session_instance = mocked_session(mock_session)

    mock_user = mock_user_object()
    mock_user.roles = [mock_role_object()]

    token_row = MagicMock()
    token_row.revoked = False
    token_row.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    mock_session_instance.execute.side_effect = [
      user_lookup_result(mock_user),
      token_lookup_result(token_row),
    ]

    mock_encode.return_value = 'new.access.token'
    mock_encode_refresh.return_value = 'new.refresh.token'
    mock_decode_refresh.side_effect = [
      {
        'sub': '1',
        'jti': 'old-jti',
        'exp': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).timestamp(),
      },
      {
        'sub': '1',
        'jti': 'new-jti',
        'exp': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).timestamp(),
      },
    ]

    service = UserService()
    result = service.refresh_user_token('old.refresh.token')

    self.assertEqual(result['status'], 'success')
    self.assertEqual(result['auth_token'], 'new.access.token')
    self.assertEqual(result['refresh_token'], 'new.refresh.token')
    self.assertTrue(token_row.revoked)

  @patch('services.userService.decode_refresh_token')
  @patch('services.userService.Session')
  def test_refresh_token_rotation_rejects_revoked_token(self, mock_session, mock_decode_refresh):
    mock_session_instance = mocked_session(mock_session)

    mock_user = mock_user_object()
    token_row = MagicMock()
    token_row.revoked = True
    token_row.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    mock_session_instance.execute.side_effect = [
      user_lookup_result(mock_user),
      token_lookup_result(token_row),
    ]
    mock_decode_refresh.return_value = {
      'sub': '1',
      'jti': 'revoked-jti',
      'exp': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).timestamp(),
    }

    service = UserService()
    with self.assertRaises(ApiError) as ctx:
      service.refresh_user_token('revoked.refresh.token')

    self.assertEqual(ctx.exception.status_code, 401)

  @patch('services.userService.decode_refresh_token')
  @patch('services.userService.Session')
  def test_revoke_refresh_token_success(self, mock_session, mock_decode_refresh):
    mock_session_instance = mocked_session(mock_session)

    token_row = MagicMock()
    token_row.revoked = False
    mock_session_instance.execute.return_value = token_lookup_result(token_row)
    mock_decode_refresh.return_value = {'sub': '1', 'jti': 'logout-jti', 'exp': 2000000000}

    service = UserService()
    result = service.revoke_refresh_token('logout.refresh.token')

    self.assertEqual(result['status'], 'success')
    self.assertTrue(token_row.revoked)

  @patch('services.userService.Session')
  def test_revoke_all_refresh_tokens_success(self, mock_session):
    mock_session_instance = mocked_session(mock_session)

    token_a = MagicMock(revoked=False)
    token_b = MagicMock(revoked=False)
    mock_session_instance.execute.return_value = token_list_result([token_a, token_b])

    service = UserService()
    result = service.revoke_all_refresh_tokens(1)

    self.assertEqual(result['status'], 'success')
    self.assertEqual(result['revoked_tokens'], 2)
    self.assertTrue(token_a.revoked)
    self.assertTrue(token_b.revoked)

  @patch('services.userService.Session')
  def test_delete_success(self, mock_session):
    mock_session_instance = mocked_session(mock_session)
    user = mock_user_object()
    mock_session_instance.execute.return_value = user_lookup_result(user)

    service = UserService()
    result = service.delete(1)

    self.assertEqual(result, 'successful')
    mock_session_instance.delete.assert_called_once_with(user)

  @patch('services.userService.Session')
  def test_delete_user_not_found(self, mock_session):
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value = user_lookup_result(None)

    service = UserService()
    result = service.delete(999)

    self.assertIsNone(result)


if __name__ == '__main__':
  unittest.main()
