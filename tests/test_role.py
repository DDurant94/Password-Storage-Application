from unittest.mock import MagicMock, patch
import unittest
import pytest
import os
import sys
import requests

from __init__ import mocked_session, create_app, mock_role_data, mock_roles_data

from models.role import Role
from services.roleService import save,update,find,delete

from models.user import User

def mock_add_role_data():
  data = {
    "role_name": "user"
  }
  return data

def role_save_url():
  data = {
    "role_name": "admin"
  }
  resp = requests.post('https://127.0.0.1:5000/roles/',json=data)
  return resp

def role_find_all_url():
  find_all_role_url = requests.get('https://127.0.0.1:5000/roles/')
  return find_all_role_url



class TestRoleEndpoint(unittest.TestCase):
  def setUp(self):
    self.app = create_app('DevelopmentConfig')
    self.app_context = self.app.app_context()
    self.app_context.push()
    
  def tearDown(self):
    self.app_context.pop()
  ##  
  ###
  #### Role Service Testing
  ###
  ##
  
  ##
  ### Save
  ##
  
  @patch('services.roleService.db.session.execute')
  @patch('services.roleService.Session')
  def test_save_role(self, mock_session,mock_execute):
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
  def test_save_exception_role_already_exsists(self,mock_session,mock_execute):
  
    mock_role = mock_role_data()
    role_data = mock_add_role_data()
    
    mock_session.return_value.__enter__.return_value = mock_session
    mock_execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_role

    with self.assertRaises(ValueError) as context:
      save(role_data)

    self.assertTrue('Role already In Database' in str(context.exception))
    mock_execute.assert_called_once()
    mock_session.assert_called_once() 
  ##
  ### Find
  ##
  @patch('services.roleService.db.session.execute')
  def test_find_roles(self,mock_execute):
    mock_roles = mock_roles_data()
    mock_admin_user_id = 1
    
    mock_execute.return_value.scalars.return_value.all.return_value = mock_roles
    
    resp = find(mock_admin_user_id)
    
    self.assertEqual(len(resp),2)
    self.assertEqual(resp[0].role_name, mock_roles[0].role_name)
    self.assertEqual(resp[1].role_name, mock_roles[1].role_name)
  ##
  ### Update
  ##
  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_update(self,mock_session,mock_select):
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

  ##
  ### Delete
  ##
  
  @patch('services.roleService.db.select')
  @patch('services.roleService.Session')
  def test_delete(self,mock_session,mock_select):
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

  @patch('services.roleService.Session')
  @patch('services.roleService.db.select')
  def test_delete_role_not_found(self, mock_select, mock_session):
    # Mock data
    role_data = {'role_id': 999, 'role_name': 'non_existent_role'}
    user_id = 123

    # Mock behavior
    mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = None
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Importing and testing
    from services.roleService import delete
    with self.assertRaises(ValueError) as context:
      delete(user_id, role_data)

    self.assertIn("Role Not Found!", str(context.exception))
    mock_session_instance.commit.assert_not_called()

  # def test_delete_restricted_role(self):
  #   with patch('services.roleService.Session') as mock_session, patch('services.roleService.db.select') as mock_select:
  #     mock_session_instance = mock_session.return_value.__enter__.return_value
  #     restricted_role_mock = MagicMock()
  #     restricted_role_mock.role_name = 'admin'
  #     mock_select.return_value.where.return_value.unique.return_value.scalar_one_or_none.return_value = restricted_role_mock
        
  #     with self.assertRaises(ValueError) as context:
  #       delete(user_id=123, role_data={'role_id': 1, 'role_name': 'admin'})
      
  #     self.assertEqual(str(context.exception), "Can not delete 'admin' role!")
  #     mock_session_instance.commit.assert_not_called()  

  ##
  ###
  #### Role Controler/URL Testing
  ###
  ##
  
  ##
  ### Find
  ##
  @patch('requests.get')
  def test_get_all_roles(self,mock_get):
    mock_return = mock_roles_data()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_return
    
    resp = role_find_all_url()
    
    mock_get.assert_called_once_with('https://127.0.0.1:5000/roles/')
    self.assertEqual(resp.status_code,200)
    self.assertEqual(resp.json(),mock_return)
       
if __name__ == '__main__':
  unittest.main()