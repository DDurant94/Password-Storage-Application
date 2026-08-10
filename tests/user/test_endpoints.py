import unittest
from unittest.mock import patch

from flask import json

from tests.helpers import BaseFlaskTest
from tests.user.test_data import mock_user_input, mock_user_object
from utils.error_handlers import ApiError


class TestUserEndpoints(BaseFlaskTest):

  @patch('controllers.userController.userService.save')
  def test_post_user_success(self, mock_save):
    mock_save.return_value = mock_user_object()

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.userController.userService.save')
  def test_post_user_already_exists(self, mock_save):
    mock_save.side_effect = ValueError('User Already Exists!')

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)

  def test_post_user_validation_error(self):
    response = self.client.post(
      '/user/',
      data=json.dumps({'username': 'usr'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.save')
  def test_post_user_circuit_breaker_fallback(self, mock_save):
    mock_save.return_value = None

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.save')
  def test_post_user_service_unavailable(self, mock_save):
    mock_save.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.post(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 503)
    data = json.loads(response.data)
    self.assertEqual(data['message'], 'Service temporarily unavailable')

  @patch('controllers.userController.userService.find_by_id')
  def test_get_user_success(self, mock_find):
    mock_find.return_value = mock_user_object()

    response = self.client.get('/user/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.userController.userService.find_by_id')
  def test_get_user_not_found(self, mock_find):
    mock_find.side_effect = ValueError('User not found!')

    response = self.client.get('/user/')

    self.assertEqual(response.status_code, 422)

  @patch('controllers.userController.userService.update')
  def test_put_user_success(self, mock_update):
    mock_update.return_value = mock_user_object()

    response = self.client.put(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.userController.userService.update')
  def test_put_user_not_found(self, mock_update):
    mock_update.side_effect = ValueError('User not Found!')

    response = self.client.put(
      '/user/',
      data=json.dumps(mock_user_input()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)

  def test_put_user_validation_error(self):
    response = self.client.put(
      '/user/',
      data=json.dumps({'username': 'usr'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.login_user')
  def test_post_login_success(self, mock_login):
    mock_login.return_value = [
      {
        'status': 'success',
        'message': 'Successfully logged in',
        'auth_token': 'fake.jwt.token',
        'refresh_token': 'fake.refresh.token'
      },
      'success'
    ]

    response = self.client.post(
      '/user/login',
      data=json.dumps({'username': 'testuser', 'password': 'TestPassword1!'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    data = json.loads(response.data)
    self.assertIn('auth_token', data)
    self.assertIn('refresh_token', data)

  @patch('controllers.userController.userService.login_user')
  def test_post_login_invalid_password(self, mock_login):
    mock_login.return_value = [None, 'Password']

    response = self.client.post(
      '/user/login',
      data=json.dumps({'username': 'testuser', 'password': 'WrongPass123!'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)

  @patch('controllers.userController.userService.login_user')
  def test_post_login_invalid_username(self, mock_login):
    mock_login.return_value = [None, 'Username']

    response = self.client.post(
      '/user/login',
      data=json.dumps({'username': 'noexist', 'password': 'TestPassword1!'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)

  @patch('controllers.userController.userService.refresh_user_token')
  def test_post_refresh_success(self, mock_refresh):
    mock_refresh.return_value = {
      'status': 'success',
      'message': 'Token refreshed successfully',
      'auth_token': 'new.jwt.token',
      'refresh_token': 'new.refresh.token'
    }

    response = self.client.post(
      '/user/refresh',
      data=json.dumps({'refresh_token': 'old.refresh.token'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)

  def test_post_refresh_missing_token(self):
    response = self.client.post(
      '/user/refresh',
      data=json.dumps({}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.refresh_user_token')
  def test_post_refresh_invalid_token(self, mock_refresh):
    mock_refresh.side_effect = ApiError('Invalid token', status_code=401)

    response = self.client.post(
      '/user/refresh',
      data=json.dumps({'refresh_token': 'bad.refresh.token'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 401)

  @patch('controllers.userController.userService.revoke_refresh_token')
  def test_post_logout_success(self, mock_logout):
    mock_logout.return_value = {'status': 'success', 'message': 'Logged out successfully'}

    response = self.client.post(
      '/user/logout',
      data=json.dumps({'refresh_token': 'token'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)

  def test_post_logout_missing_token(self):
    response = self.client.post(
      '/user/logout',
      data=json.dumps({}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)

  @patch('controllers.userController.userService.revoke_all_refresh_tokens')
  def test_post_logout_all_success(self, mock_logout_all):
    mock_logout_all.return_value = {
      'status': 'success',
      'message': 'Logged out from all devices',
      'revoked_tokens': 2
    }

    response = self.client.post('/user/logout-all')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.userController.userService.delete')
  def test_delete_user_success(self, mock_delete):
    mock_delete.return_value = 'successful'

    response = self.client.delete('/user/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.userController.userService.delete')
  def test_delete_user_not_found(self, mock_delete):
    mock_delete.return_value = None

    response = self.client.delete('/user/')

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
