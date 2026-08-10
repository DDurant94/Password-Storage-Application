from unittest.mock import patch, MagicMock

import unittest

from services.folderService import save, find_user_folders, update, delete
from tests.folder.test_data import mock_folder_data, mock_folder_object
from tests.helpers import BaseFlaskTest, mocked_session


class TestFolderService(BaseFlaskTest):

  @patch('services.folderService.time')
  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_time):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_time.return_value = 'now'

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.scalar_one_or_none.return_value = None

    result = save(1, mock_folder_data())

    self.assertIsNotNone(result)
    self.assertEqual(result.folder_name, 'Personal')

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_save_duplicate_name(self, mock_session, mock_find_user):
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
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = find_user_folders(1)

    self.assertIsNone(result)

  @patch('services.folderService.db.session.query')
  @patch('services.folderService.find_user')
  def test_find_user_folders_success(self, mock_find_user, mock_query):
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
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    folder = mock_folder_object()
    child = MagicMock()
    child.parent_folder_id = 99
    folder.children_folders = [child]

    session_instance = mocked_session(mock_session)
    query_result = MagicMock()
    query_result.unique.return_value.scalar_one_or_none.return_value = folder
    session_instance.execute.return_value = query_result

    result = delete(1, mock_folder_data())

    self.assertEqual(result, 'successful')
    self.assertEqual(child.parent_folder_id, folder.parent_folder_id)
    session_instance.delete.assert_called_once_with(folder)

  @patch('services.folderService.find_user')
  @patch('services.folderService.Session')
  def test_delete_detaches_linked_passwords(self, mock_session, mock_find_user):
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    folder = mock_folder_object()
    folder.folder_id = 7
    password = MagicMock()
    password.folder_id = folder.folder_id

    session_instance = mocked_session(mock_session)
    folder_result = MagicMock()
    folder_result.unique.return_value.scalar_one_or_none.return_value = folder
    password_result = MagicMock()
    password_result.scalars.return_value.all.return_value = [password]
    session_instance.execute.side_effect = [folder_result, password_result]

    result = delete(1, mock_folder_data())

    self.assertEqual(result, 'successful')
    self.assertIsNone(password.folder_id)
    session_instance.delete.assert_called_once_with(folder)


if __name__ == '__main__':
  unittest.main()
