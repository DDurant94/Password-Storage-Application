import datetime
from unittest.mock import MagicMock

from models.role import Role
from models.user import User


def mock_user_input():
  return {
    "username": "testuser",
    "password": "TestPassword1!",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }


def mock_user_update_input():
  return {
    "username": "testuser",
    "password": "TestPassword1!",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com"
  }


def mock_user_object():
  user = MagicMock(spec=User)
  user.user_id = 1
  user.username = "testuser"
  user.password = "hashed_password"
  user.first_name = "John"
  user.last_name = "Doe"
  user.email = "john.doe@example.com"
  user.role = "user"
  user.roles = []
  user.key = b"\x00" * 16
  user.create_date = datetime.datetime.now()
  user.updated_date = datetime.datetime.now()
  return user


def mock_role_object():
  role = MagicMock(spec=Role)
  role.role_id = 1
  role.role_name = "user"
  return role


def user_lookup_result(user):
  result = MagicMock()
  result.unique.return_value.scalar_one_or_none.return_value = user
  return result


def role_lookup_result(role):
  result = MagicMock()
  result.scalar_one_or_none.return_value = role
  return result


def token_lookup_result(token_row):
  result = MagicMock()
  result.scalar_one_or_none.return_value = token_row
  return result


def token_list_result(tokens):
  result = MagicMock()
  result.scalars.return_value.all.return_value = tokens
  return result
