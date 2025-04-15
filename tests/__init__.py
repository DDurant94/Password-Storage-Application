from unittest.mock import MagicMock, patch
import unittest

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

from models.user import User
from services.userService import save,update,delete,find_by_id

from models.role import Role
from services.roleService import save,update,find,delete

from models.folder import Folder
from services.folderService import save,update,find_user_folders,delete

from models.passwords import Password
from services.passwordService import save, find_password, find_passwords, update, delete

from models.passwordHist import PasswordHistory
from services.passwordHistService import find_password_history, find_passwords_history

from models.auditLog import AuditLog
from services.auditLogService import find

from models.securityQuestion import SecurityQuestion
from services.securityQuestionService import save,find,update,delete


def mocked_session(mock_session):
  return mock_session.return_value.__enter__.return_value

def mock_role_data():
  mock_role = MagicMock(spec=Role)
  mock_role.id = 1
  mock_role.role_name = 'user'
  return mock_role

def mock_roles_data():
  mock_role1 = MagicMock(spec=Role)
  mock_role1.id = 1
  mock_role1.role_name = "admin"

  mock_role2 = MagicMock(spec=Role)
  mock_role2.id = 2
  mock_role2.role_name = "user"
  
  return [mock_role1,mock_role2]

def role_NF_data():
  
  role_data={'role_id': 999,
            'role_name': 'non_existent_role'}
  return role_data