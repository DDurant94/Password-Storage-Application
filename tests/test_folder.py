import datetime

from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.folder import Folder
from services.folderService import save, find_user_folders, update, delete
from tests.helpers import BaseFlaskTest, mocked_session


def mock_folder_data():
  """Return valid folder request payload data."""
  return {
    'folder_id': 1,
    'user_id': 1,
    'parent_folder_id': None,
    'folder_name': 'Personal'
  }


def mock_folder_object():
  """Return a mock Folder object with required schema fields."""
  folder = MagicMock(spec=Folder)
  folder.folder_id = 1
  folder.user_id = 1
  folder.parent_folder_id = None
  folder.folder_name = 'Personal'
  folder.created_date = datetime.datetime.now()
  folder.children_folders = []
  return folder


class TestFolderService(BaseFlaskTest):

  @patch('services.folderService.time')
  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_time):
    """Saving a folder succeeds when name is unique and parent is valid."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_time.return_value = 'now'

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.scalar_one_or_none.return_value = None

    result = save(1, mock_folder_data())

    self.assertIsNotNone(result)
    self.assertEqual(result.folder_name, 'Personal')
    session_instance.commit.assert_called_once()

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_save_duplicate_name(self, mock_session, mock_find_user):
    """Saving a folder with duplicate name raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.scalar_one_or_none.return_value = mock_folder_object()

    with self.assertRaises(ValueError) as context:
      save(1, mock_folder_data())

    self.assertIn('Folder name should be unique', str(context.exception))

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_save_parent_not_found(self, mock_session, mock_find_user):
    """Saving with a missing parent_folder_id raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    existing_check = MagicMock()
    existing_check.scalar_one_or_none.return_value = None
    parent_check = MagicMock()
    parent_check.scalar_one_or_none.return_value = None
    session_instance.execute.side_effect = [existing_check, parent_check]

    payload = mock_folder_data()
    payload['parent_folder_id'] = 99

    with self.assertRaises(ValueError) as context:
      save(1, payload)

    self.assertIn("Parent folder doesn't exist", str(context.exception))

  @patch('services.folderService.db.session.query')
  @patch('services.folderService.find_user')
  def test_find_user_folders_none(self, mock_find_user, mock_query):
    """Finding user folders returns None when no folders exist."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = find_user_folders(1)

    self.assertIsNone(result)

  @patch('services.folderService.db.session.query')
  @patch('services.folderService.find_user')
  def test_find_user_folders_success(self, mock_find_user, mock_query):
    """Finding user folders returns the folder list."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    folders = [mock_folder_object()]
    mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = folders

    result = find_user_folders(1)

    self.assertEqual(result, folders)

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_update_folder_not_found(self, mock_session, mock_find_user):
    """Updating a missing folder raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    folder_check = MagicMock()
    folder_check.unique.return_value.scalar_one_or_none.return_value = None
    session_instance.execute.return_value = folder_check

    with self.assertRaises(ValueError) as context:
      update(1, mock_folder_data())

    self.assertIn('Folder not found!', str(context.exception))

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_update_name_conflict(self, mock_session, mock_find_user):
    """Updating to a duplicate folder name raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    folder = mock_folder_object()
    folder.folder_id = 1
    duplicate = mock_folder_object()
    duplicate.folder_id = 2

    session_instance = mocked_session(mock_session)
    folder_result = MagicMock()
    folder_result.unique.return_value.scalar_one_or_none.return_value = folder
    duplicate_result = MagicMock()
    duplicate_result.unique.return_value.scalar_one_or_none.return_value = duplicate
    session_instance.execute.side_effect = [folder_result, duplicate_result]

    with self.assertRaises(ValueError) as context:
      update(1, mock_folder_data())

    self.assertIn('Folder name should be unique', str(context.exception))

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_update_success(self, mock_session, mock_find_user):
    """Updating folder fields and children relationships succeeds."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    folder = mock_folder_object()
    child = MagicMock()
    child.parent_folder_id = None
    folder.children_folders = [child]

    session_instance = mocked_session(mock_session)
    folder_result = MagicMock()
    folder_result.unique.return_value.scalar_one_or_none.return_value = folder
    unique_name_result = MagicMock()
    unique_name_result.unique.return_value.scalar_one_or_none.return_value = None
    session_instance.execute.side_effect = [folder_result, unique_name_result]

    payload = mock_folder_data()
    payload['folder_name'] = 'Work'

    result = update(1, payload)

    self.assertEqual(result.folder_name, 'Work')
    self.assertEqual(child.parent_folder_id, folder.folder_id)

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_delete_not_found(self, mock_session, mock_find_user):
    """Deleting a missing folder returns None."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    query_result = MagicMock()
    query_result.unique.return_value.scalar_one_or_none.return_value = None
    session_instance.execute.return_value = query_result

    result = delete(1, mock_folder_data())

    self.assertIsNone(result)

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_delete_success(self, mock_session, mock_find_user):
    """Deleting an existing folder returns successful."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    query_result = MagicMock()
    query_result.unique.return_value.scalar_one_or_none.return_value = mock_folder_object()
    session_instance.execute.return_value = query_result

    result = delete(1, mock_folder_data())

    self.assertEqual(result, 'successful')
    session_instance.delete.assert_called_once()


class TestFolderEndpoints(BaseFlaskTest):

  @patch('controllers.folderController.folderService.save')
  def test_post_folder_success(self, mock_save):
    """POST /folder/ returns 201 on successful create."""
    mock_save.return_value = mock_folder_object()

    response = self.client.post(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_folder_validation_error(self):
    """POST /folder/ returns 400 for invalid payload."""
    response = self.client.post('/folder/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.folderController.folderService.find_user_folders')
  def test_get_folders_success(self, mock_find):
    """GET /folder/ returns 200 when folders exist."""
    mock_find.return_value = [mock_folder_object()]

    response = self.client.get('/folder/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.folderController.folderService.find_user_folders')
  def test_get_folders_not_found(self, mock_find):
    """GET /folder/ returns 404 when folders are missing."""
    mock_find.return_value = None

    response = self.client.get('/folder/')

    self.assertEqual(response.status_code, 404)

  @patch('controllers.folderController.folderService.update')
  def test_put_folder_success(self, mock_update):
    """PUT /folder/ returns 201 when update succeeds."""
    mock_update.return_value = mock_folder_object()

    response = self.client.put(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.folderController.folderService.update')
  def test_put_folder_error(self, mock_update):
    """PUT /folder/ returns 422 on service error."""
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
    """DELETE /folder/ returns 200 when delete succeeds."""
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
    """DELETE /folder/ returns 404 when folder does not exist."""
    mock_delete.return_value = None

    response = self.client.delete(
      '/folder/',
      data=json.dumps(mock_folder_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
