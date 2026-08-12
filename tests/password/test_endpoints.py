from unittest.mock import patch

import unittest
from flask import json

from tests.helpers import BaseFlaskTest
from tests.password.test_data import mock_password_data, mock_password_object
from utils.errorHandlers import ApiError


class TestPasswordEndpoints(BaseFlaskTest):

  @patch('controllers.passwordController.passwordService.save')
  def test_post_password_success(self, mock_save):
    mock_save.return_value = mock_password_object()

    response = self.client.post(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_password_validation_error(self):
    response = self.client.post('/password/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.passwordController.passwordService.save')
  def test_post_password_service_unavailable(self, mock_save):
    mock_save.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.post(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 503)
    self.assertIn('Service temporarily unavailable', response.get_data(as_text=True))

  @patch('controllers.passwordController.passwordService.find_passwords')
  def test_get_passwords_success(self, mock_find):
    mock_find.return_value = [mock_password_object()]

    response = self.client.get('/password/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.passwordController.passwordService.find_passwords')
  def test_get_passwords_accepts_limit_and_offset(self, mock_find):
    mock_find.return_value = [mock_password_object()]

    response = self.client.get('/password/?limit=10&offset=5')

    self.assertEqual(response.status_code, 200)
    self.assertEqual(mock_find.call_args.kwargs['limit'], 10)
    self.assertEqual(mock_find.call_args.kwargs['offset'], 5)

  @patch('controllers.passwordController.passwordService.find_password')
  def test_get_password_by_name_not_found(self, mock_find):
    mock_find.return_value = None

    response = self.client.get('/password/search=Nope')

    self.assertEqual(response.status_code, 404)
    self.assertIn("Couldn't find 'Nope'", response.get_data(as_text=True))

  @patch('controllers.passwordController.passwordService.find_password')
  def test_get_password_by_name_success(self, mock_find):
    mock_find.return_value = mock_password_object()

    response = self.client.get('/password/search=Github')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.passwordController.passwordService.update')
  def test_put_password_success(self, mock_update):
    mock_update.return_value = mock_password_object()

    response = self.client.put(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.passwordController.passwordService.update')
  def test_put_password_error(self, mock_update):
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
    mock_delete.return_value = None

    response = self.client.delete(
      '/password/',
      data=json.dumps(mock_password_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
