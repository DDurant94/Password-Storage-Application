from unittest.mock import MagicMock, patch

import unittest

from models.role import Role
from models.user import User
from services.roleService import delete, find, save, update
from tests.helpers import BaseFlaskTest, mocked_session
from tests.role.test_data import (
  mock_add_role_data,
  mock_role_data,
  mock_roles_data,
  role_not_found_data,
)


raw_save = save.__wrapped__


class TestRoleService(BaseFlaskTest):

  def setUp(self):
    super().setUp()
    from services.roleService import role_service
    role_service.clear_cache()

  @patch('services.roleService.Session')
  def test_save_role(self, mock_session):
    role_data = mock_add_role_data()
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    response = raw_save(role_data)

    self.assertIsNotNone(response)
    self.assertEqual(response.role_name, role_data['role_name'])
    mock_session_instance.execute.assert_called_once()

  @patch('services.roleService.Session')
  def test_save_exception_role_already_exists(self, mock_session):
    role_data = mock_add_role_data()
    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_role_data()

    with self.assertRaises(ValueError) as context:
      raw_save(role_data)

    self.assertIn('Role already In Database', str(context.exception))
    mock_session_instance.execute.assert_called_once()

  @patch('services.roleService.db.session.execute')
  def test_find_all_roles(self, mock_execute):
    expected = mock_roles_data()
    mock_execute.return_value.scalars.return_value.all.return_value = expected

    response = find(user_id=1)

    self.assertEqual(len(response), 2)
    self.assertEqual(response[0].role_name, expected[0].role_name)
    self.assertEqual(response[1].role_name, expected[1].role_name)

  @patch('services.roleService.db.session.execute')
  def test_find_roles_empty(self, mock_execute):
    mock_execute.return_value.scalars.return_value.all.return_value = []

    response = find(user_id=1)

    self.assertEqual(response, [])

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_update(self, mock_session, mock_select):
    role_data = {'role_id': 1, 'role_name': 'new_role_name'}
    user_mock = MagicMock(spec=User)
    user_mock.role = 'old_role_name'
    role_mock = MagicMock(spec=Role)
    role_mock.role_name = 'old_role_name'

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.query.return_value.where.return_value.all.return_value = [user_mock]
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock

    response = update(user_id=123, role_data=role_data)

    self.assertIsNotNone(response)
    self.assertEqual(response.role_name, role_data['role_name'])
    self.assertEqual(user_mock.role, role_data['role_name'])
    mock_session_instance.refresh.assert_called_once_with(response)

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_update_role_not_found(self, mock_session, mock_select):
    role_data = role_not_found_data()

    mock_session_instance = mocked_session(mock_session)
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = None
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    with self.assertRaises(ValueError) as context:
      update(123, role_data)

    self.assertIn('Role Not Found!', str(context.exception))

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete(self, mock_session, mock_select):
    role_data = {'role_id': 1, 'role_name': 'test_role'}
    user_mock = MagicMock()
    user_mock.role = 'test_role'
    role_mock = MagicMock()
    role_mock.role_name = 'test_role'
    user_role_mock = MagicMock()
    user_role_mock.role_name = 'user'
    umr_mock = MagicMock()

    mock_session_instance = mocked_session(mock_session)
    mock_session_instance.query.return_value.where.return_value.one_or_none.side_effect = [user_role_mock]
    mock_session_instance.query.return_value.where.return_value.all.return_value = [user_mock]
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.side_effect = [role_mock]
    mock_session_instance.execute.return_value.scalars.return_value.all.return_value = [umr_mock]

    response = delete(123, role_data)

    self.assertEqual(response, 'successful')
    self.assertEqual(user_mock.role, 'user')
    self.assertEqual(umr_mock.role_id, user_role_mock.role_id)
    mock_session_instance.delete.assert_called_once()

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_role_not_found(self, mock_session, mock_select):
    role_data = role_not_found_data()

    mock_session_instance = mocked_session(mock_session)
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = None
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    with self.assertRaises(ValueError) as context:
      delete(123, role_data)

    self.assertIn('Role Not Found!', str(context.exception))

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_restricted_role_admin(self, mock_session, mock_select):
    role_mock = MagicMock()
    role_mock.role_name = 'admin'

    mock_session_instance = mocked_session(mock_session)
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock

    with self.assertRaises(ValueError) as context:
      delete(123, {'role_id': 1, 'role_name': 'admin'})

    self.assertEqual(str(context.exception), "Can not delete 'admin' role!")

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_restricted_role_user(self, mock_session, mock_select):
    role_mock = MagicMock()
    role_mock.role_name = 'user'

    mock_session_instance = mocked_session(mock_session)
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock

    with self.assertRaises(ValueError) as context:
      delete(123, {'role_id': 2, 'role_name': 'user'})

    self.assertEqual(str(context.exception), "Can not delete 'user' role!")


if __name__ == '__main__':
  unittest.main()
