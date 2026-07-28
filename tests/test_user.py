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
from services.userService import save, update, find_user, delete

def mocked_session(mock_session):
  """Return the mock session context manager."""
  return mock_session.return_value.__enter__.return_value
