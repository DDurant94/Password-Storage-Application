"""
Unit and endpoint tests for the Role service and API endpoints.

- Service layer tests mock the DB/session and test business logic.
- Endpoint tests use Flask's test client and patch authentication decorators.
- All authentication decorators are patched at the top to bypass auth in tests.
- Shared setup/teardown via BaseFlaskTest.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from functools import wraps

# --- Patch authentication decorators before any app/controller import ---

def fake_token_required(f):
  """Bypass token auth and inject a dummy user_id."""
  @wraps(f)
  def wrapper(*args, **kwargs):
    import inspect
    sig = inspect.signature(f)
    if 'user_id' in sig.parameters and 'user_id' not in kwargs:
      return f(user_id=1, *args, **kwargs)
    return f(*args, **kwargs)
  return wrapper

def fake_role_required(role):
  """Bypass role auth."""
  def decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)
    return wrapper
  return decorator

patch('utils.utils.token_required', fake_token_required).start()
patch('utils.utils.role_required', fake_role_required).start()

import unittest
from flask import json
from app import create_app
from models.role import Role
from models.user import User
from services.roleService import save, update, find, delete

def mocked_session(mock_session):
  """Return the mock session context manager."""
  return mock_session.return_value.__enter__.return_value

def mock_role_data():
  """Return a mock Role object."""
  mock_role = MagicMock(spec=Role)
  mock_role.id = 1
  mock_role.role_name = 'user'
  return mock_role

def mock_roles_data():
  """Return a list of mock Role objects."""
  mock_role1 = MagicMock(spec=Role)
  mock_role1.id = 1
  mock_role1.role_name = "admin"
  mock_role2 = MagicMock(spec=Role)
  mock_role2.id = 2
  mock_role2.role_name = "user"
  return [mock_role1, mock_role2]

def role_NF_data():
  """Return data for a non-existent role."""
  return {'role_id': 999, 'role_name': 'non_existent_role'}

def mock_add_role_data():
  """Return data for adding a new role."""
  return {"role_name": "user"}

# --- Shared Base Test Class ---

class BaseFlaskTest(unittest.TestCase):
  """Base test class to set up Flask app and context."""

  def setUp(self):
    self.app = create_app('TestingConfig')
    self.client = self.app.test_client()
    self.ctx = self.app.app_context()
    self.ctx.push()

  def tearDown(self):
    self.ctx.pop()

# --- Service Layer Tests ---

class TestRoleService(BaseFlaskTest):
  
  @patch('services.roleService.db.session.execute')
  @patch('services.roleService.Session')
  def test_save_role(self, mock_session, mock_execute):
    """Saving a new role successfully."""
    role_data = mock_add_role_data()
    
    mock_session.return_value.__enter__.return_value = mock_session
    mock_execute.return_value.unique.return_value.scalar_one_or_none.return_value = None
    
    resp = save(role_data)
    
    self.assertIsNotNone(resp)
    self.assertEqual(resp.role_name, role_data['role_name'])
    
    mock_execute.assert_called_once()
    mock_session.assert_called_once()

  @patch('services.roleService.db.session.execute')
  @patch('services.roleService.Session')
  def test_save_exception_role_already_exists(self, mock_session, mock_execute):
    """Saving a role that already exists raises ValueError."""
    mock_role = mock_role_data()
    role_data = mock_add_role_data()
    
    mock_session.return_value.__enter__.return_value = mock_session
    mock_execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_role
    
    with self.assertRaises(ValueError) as context:
        save(role_data)
        
    self.assertIn('Role already In Database', str(context.exception))
    
    mock_execute.assert_called_once()
    mock_session.assert_called_once()

  @patch('services.roleService.db.session.execute')
  def test_find_all_roles(self, mock_execute):
    """Finding all roles returns the correct list."""
    mock_roles = mock_roles_data()
    
    mock_execute.return_value.scalars.return_value.all.return_value = mock_roles
    
    resp = find(user_id=1)
    
    self.assertEqual(len(resp), 2)
    self.assertEqual(resp[0].role_name, mock_roles[0].role_name)
    self.assertEqual(resp[1].role_name, mock_roles[1].role_name)

  @patch('services.roleService.db.session.execute')
  def test_find_roles_empty(self, mock_execute):
    """Finding roles when none exist returns an empty list."""
    mock_execute.return_value.scalars.return_value.all.return_value = []
    
    resp = find(user_id=1)
    
    self.assertEqual(resp, [])

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_update(self, mock_session, mock_select):
    """Updating a role and updating users with that role."""
    role_data = {'role_id': 1, 'role_name': 'new_role_name'}
    user_mock = MagicMock(spec=User)
    user_mock.role = 'old_role_name'
    role_mock = MagicMock(spec=Role)
    role_mock.role_name = 'old_role_name'
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_session_instance.query.return_value.where.return_value.all.return_value = [user_mock]
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    
    resp = update(user_id=123, role_data=role_data)
    
    self.assertIsNotNone(resp)
    self.assertEqual(resp.role_name, role_data['role_name'])
    self.assertEqual(user_mock.role, role_data['role_name'])
    
    mock_session_instance.commit.assert_called_once()
    mock_session_instance.refresh.assert_called_once_with(resp)

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_update_role_not_found(self, mock_session, mock_select):
    """Updating a non-existent role raises ValueError."""
    role_data = role_NF_data()
    user_id = 123
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = None
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None
    
    with self.assertRaises(ValueError) as context:
        update(user_id, role_data)
        
    self.assertIn("Role Not Found!", str(context.exception))
    
    mock_session_instance.commit.assert_not_called()

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete(self, mock_session, mock_select):
    """Deleting a role and reassigning users and management roles."""
    role_data = {'role_id': 1, 'role_name': 'test_role'}
    user_mock = MagicMock()
    user_mock.role = 'test_role'
    role_mock = MagicMock()
    role_mock.role_name = 'test_role'
    user_role_mock = MagicMock()
    user_role_mock.role_name = 'user'
    umr_mock = MagicMock()
    user_id = 123
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_session_instance.query.return_value.where.return_value.one_or_none.side_effect = [user_role_mock]
    mock_session_instance.query.return_value.where.return_value.all.return_value = [user_mock]
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.side_effect = [role_mock]
    mock_session_instance.execute.return_value.scalars.return_value.all.return_value = [umr_mock]
    
    resp = delete(user_id, role_data)
    
    self.assertEqual(resp, 'successful')
    self.assertEqual(user_mock.role, 'user')
    self.assertEqual(umr_mock.role_id, user_role_mock.role_id)
    
    mock_session_instance.delete.assert_called_once()
    mock_session_instance.commit.assert_called_once()

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_role_not_found(self, mock_session, mock_select):
    """Deleting a non-existent role raises ValueError."""
    role_data = role_NF_data()
    user_id = 123
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = None
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None
    
    with self.assertRaises(ValueError) as context:
        delete(user_id, role_data)
        
    self.assertIn("Role Not Found!", str(context.exception))
    
    mock_session_instance.commit.assert_not_called()

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_restricted_role_admin(self, mock_session, mock_select):
    """Deleting the 'admin' role raises ValueError."""
    role_data = {'role_id': 1, 'role_name': 'admin'}
    user_id = 123
    role_mock = MagicMock()
    role_mock.role_name = 'admin'
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    
    with self.assertRaises(ValueError) as context:
        delete(user_id, role_data)
        
    self.assertEqual(str(context.exception), "Can not delete 'admin' role!")
    
    mock_session_instance.commit.assert_not_called()

  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete_restricted_role_user(self, mock_session, mock_select):
    """Deleting the 'user' role raises ValueError."""
    role_data = {'role_id': 2, 'role_name': 'user'}
    user_id = 123
    role_mock = MagicMock()
    role_mock.role_name = 'user'
    
    mock_session_instance = mocked_session(mock_session)
    
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    mock_session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = role_mock
    
    with self.assertRaises(ValueError) as context:
        delete(user_id, role_data)
        
    self.assertEqual(str(context.exception), "Can not delete 'user' role!")
    
    mock_session_instance.commit.assert_not_called()

# --- Endpoint Tests ---

class TestRoleEndpoints(BaseFlaskTest):
  """Endpoint tests for /roles/ API endpoints."""

  @patch('controllers.roleController.roleService.save')
  def test_post_role_already_exists(self, mock_save):
    """POST /roles/ returns 422 if role exists."""
    mock_save.side_effect = ValueError("Role already In Database")
    
    response = self.client.post(
        '/roles/',
        data=json.dumps({'role_name': 'user'}),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 422)
    self.assertIn('Role already In Database', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.update')
  def test_update_role_success(self, mock_update):
    """PUT /roles/ updates a role."""
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
    """PUT /roles/ returns 422 if role not found."""
    mock_update.side_effect = ValueError("Role Not Found!")
    
    response = self.client.put(
        '/roles/',
        data=json.dumps(role_NF_data()),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 422)
    self.assertIn('Role Not Found!', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_success(self, mock_delete):
    """DELETE /roles/ deletes a role."""
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
    """DELETE /roles/ returns 422 if role not found."""
    mock_delete.side_effect = ValueError("Role Not Found!")
    
    response = self.client.delete(
        '/roles/',
        data=json.dumps(role_NF_data()),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 422)
    self.assertIn('Role Not Found!', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.find')
  def test_get_roles_success(self, mock_find):
    """GET /roles/ returns all roles."""
    mock_find.return_value = [mock_role_data(), mock_role_data()]
    
    response = self.client.get('/roles/')
    
    self.assertEqual(response.status_code, 200)

  @patch('controllers.roleController.roleService.find')
  def test_get_roles_error(self, mock_find):
    """GET /roles/ returns 422 on error."""
    mock_find.side_effect = ValueError("Some error")
    
    response = self.client.get('/roles/')
    
    self.assertEqual(response.status_code, 422)
    self.assertIn('Some error', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.save')
  def test_post_role_success(self, mock_save):
    """POST /roles/ creates a new role."""
    mock_role = mock_role_data()
    
    mock_save.return_value = mock_role
    
    response = self.client.post(
        '/roles/',
        data=json.dumps({'role_name': 'user'}),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 201)
    self.assertIn('user', response.get_data(as_text=True))

  def test_post_role_validation_error(self):
    """POST /roles/ returns 400 if required field is missing."""
    response = self.client.post(
        '/roles/',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.update')
  def test_put_role_validation_error(self, mock_update):
    """PUT /roles/ returns 400 if required field is missing."""
    response = self.client.put(
        '/roles/',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_validation_error(self, mock_delete):
    """DELETE /roles/ returns 400 if required field is missing."""
    response = self.client.delete(
        '/roles/',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    self.assertEqual(response.status_code, 400)
    self.assertIn('role_name', response.get_data(as_text=True))

  @patch('controllers.roleController.roleService.delete')
  def test_delete_role_forbidden(self, mock_delete):
    """DELETE /roles/ returns 422 if forbidden role is deleted."""
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