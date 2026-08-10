from unittest.mock import MagicMock

from models.role import Role


def mock_role_data():
  role = MagicMock(spec=Role)
  role.id = 1
  role.role_name = 'user'
  return role


def mock_roles_data():
  role_1 = MagicMock(spec=Role)
  role_1.id = 1
  role_1.role_name = 'admin'

  role_2 = MagicMock(spec=Role)
  role_2.id = 2
  role_2.role_name = 'user'

  return [role_1, role_2]


def role_not_found_data():
  return {'role_id': 999, 'role_name': 'non_existent_role'}


def mock_add_role_data():
  return {'role_name': 'user'}
