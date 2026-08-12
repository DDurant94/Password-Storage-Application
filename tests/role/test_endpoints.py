from unittest.mock import patch

import unittest
from flask import json

from tests.helpers import BaseFlaskTest
from tests.role.test_data import mock_role_data, role_not_found_data
from utils.errorHandlers import ApiError


class TestRoleEndpoints(BaseFlaskTest):

  @patch('controllers.roleController.roleService.save')
  def test_post_role_already_exists(self, mock_save):
    mock_save.side_effect = ValueError('Role already In Database')

    response = self.client.post(
      '/roles/',
      data=json.dumps({'role_name': 'user'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Role already In Database', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.save')
  def test_post_role_service_unavailable(self, mock_save):
    mock_save.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.post(
      '/roles/',
      data=json.dumps({'role_name': 'user'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 503)
    self.assertIn('Service temporarily unavailable', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.update')
  def test_update_role_success(self, mock_update):
    updated_role = mock_role_data()
    updated_role.role_name = 'manager'
    mock_update.return_value = updated_role

    response = self.client.put(
      '/roles/',
      data=json.dumps({'role_id': 1, 'role_name': 'manager'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)
    self.assertIn('manager', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.update')
  def test_update_role_not_found(self, mock_update):
    mock_update.side_effect = ValueError('Role Not Found!')

    response = self.client.put(
      '/roles/',
      data=json.dumps(role_not_found_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Role Not Found!', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_success(self, mock_delete):
    mock_delete.return_value = 'successful'

    response = self.client.delete(
      '/roles/',
      data=json.dumps({'role_id': 1, 'role_name': 'admin'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn('Role removed successfully', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_not_found(self, mock_delete):
    mock_delete.side_effect = ValueError('Role Not Found!')

    response = self.client.delete(
      '/roles/',
      data=json.dumps(role_not_found_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Role Not Found!', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.find')
  def test_get_roles_success(self, mock_find):
    mock_find.return_value = [mock_role_data(), mock_role_data()]

    response = self.client.get('/roles/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.roleController.roleService.find')
  def test_get_roles_error(self, mock_find):
    mock_find.side_effect = ValueError('Some error')

    response = self.client.get('/roles/')

    self.assertEqual(response.status_code, 422)
    self.assertIn('Some error', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.save')
  def test_post_role_success(self, mock_save):
    mock_save.return_value = mock_role_data()

    response = self.client.post(
      '/roles/',
      data=json.dumps({'role_name': 'user'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)
    self.assertIn('user', response.get_data(as_text=True))

  def test_post_role_validation_error(self):
    response = self.client.post(
      '/roles/',
      data=json.dumps({}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.update')
  def test_put_role_validation_error(self, mock_update):
    response = self.client.put(
      '/roles/',
      data=json.dumps({}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_validation_error(self, mock_delete):
    response = self.client.delete(
      '/roles/',
      data=json.dumps({}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_forbidden(self, mock_delete):
    mock_delete.side_effect = ValueError("Can not delete 'admin' role!")

    response = self.client.delete(
      '/roles/',
      data=json.dumps({'role_id': 1, 'role_name': 'admin'}),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn("Can not delete 'admin' role!", response.get_data(as_text=True))


if __name__ == '__main__':
  unittest.main()
