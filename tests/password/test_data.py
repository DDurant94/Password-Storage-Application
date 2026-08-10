import datetime
from unittest.mock import MagicMock

from models.passwords import Password


def mock_password_data():
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
