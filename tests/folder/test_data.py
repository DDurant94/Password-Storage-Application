import datetime
from unittest.mock import MagicMock

from models.folder import Folder


def mock_folder_data():
  return {
    'folder_id': 1,
    'user_id': 1,
    'parent_folder_id': None,
    'folder_name': 'Personal'
  }


def mock_folder_object():
  folder = MagicMock(spec=Folder)
  folder.folder_id = 1
  folder.user_id = 1
  folder.parent_folder_id = None
  folder.folder_name = 'Personal'
  folder.created_date = datetime.datetime.now()
  folder.children_folders = []
  return folder
