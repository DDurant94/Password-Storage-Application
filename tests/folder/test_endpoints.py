from unittest.mock import patch

import unittest
from flask import json

from tests.folder.test_data import mock_folder_data, mock_folder_object
from tests.helpers import BaseFlaskTest
from utils.error_handlers import ApiError


class TestFolderEndpoints(BaseFlaskTest):

  @patch('controllers.folderController.folderService.save')
  def test_post_folder_success(self, mock_save):
    mock_save.return_value = mock_folder_object()

    response = self.client.post(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_folder_validation_error(self):
    response = self.client.post('/folder/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.folderController.folderService.save')
  def test_post_folder_service_unavailable(self, mock_save):
    mock_save.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.post(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 503)
    self.assertIn('Service temporarily unavailable', response.get_data(as_text=True))

  @patch('controllers.folderController.folderService.find_user_folders')
  def test_get_folders_success(self, mock_find):
    mock_find.return_value = [mock_folder_object()]

    response = self.client.get('/folder/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.folderController.folderService.find_user_folders')
  def test_get_folders_not_found(self, mock_find):
    mock_find.return_value = None

    response = self.client.get('/folder/')

    self.assertEqual(response.status_code, 404)

  @patch('controllers.folderController.folderService.update')
  def test_put_folder_success(self, mock_update):
    mock_update.return_value = mock_folder_object()

    response = self.client.put(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.folderController.folderService.update')
  def test_put_folder_error(self, mock_update):
    mock_update.side_effect = ValueError('Folder not found!')

    response = self.client.put(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Folder not found!', response.get_data(as_text=True))

  @patch('controllers.folderController.folderService.delete')
  def test_delete_folder_success(self, mock_delete):
    mock_delete.return_value = 'successful'

    response = self.client.delete(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn('Folder has be removed!', response.get_data(as_text=True))

  @patch('controllers.folderController.folderService.delete')
  def test_delete_folder_not_found(self, mock_delete):
    mock_delete.return_value = None

    response = self.client.delete(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
