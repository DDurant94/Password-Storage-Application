import inspect
import os
import sys
from functools import wraps
from pathlib import Path
from unittest.mock import patch

import pytest

"""Configure Testing"""

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

# Explicit import so patch target resolution works reliably in Python 3.13+.
import utils.utils  # noqa: F401


_PATCHERS = []


def fake_token_required(f):
  """Bypass token auth and inject a dummy user_id for protected endpoints."""
  @wraps(f)
  def wrapper(*args, **kwargs):
    sig = inspect.signature(f)
    if 'user_id' in sig.parameters and 'user_id' not in kwargs:
      return f(user_id=1, *args, **kwargs)
    return f(*args, **kwargs)

  return wrapper


def fake_role_required(role):
  """Bypass role auth for endpoint tests."""
  def decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)

    return wrapper

  return decorator


def pytest_configure(config):
  """Register markers and patch auth once for the full test session."""
  config.addinivalue_line('markers', 'unit: fast unit/service tests')
  config.addinivalue_line('markers', 'api: in-process HTTP endpoint tests')
  config.addinivalue_line('markers', 'contract: cross-service or external API contract tests')

  _PATCHERS.extend(
    [
      patch('utils.utils.token_required', fake_token_required),
      patch('utils.utils.role_required', fake_role_required),
    ]
  )
  for patcher in _PATCHERS:
    patcher.start()


def pytest_unconfigure(config):
  """Stop global patchers cleanly at session end."""
  for patcher in _PATCHERS:
    patcher.stop()
  _PATCHERS.clear()


def pytest_collection_modifyitems(config, items):
  """Auto-label tests so service vs API vs contract subsets are easy to run."""
  for item in items:
    nodeid = item.nodeid
    if 'tests/contracts/' in nodeid.replace('\\', '/'):
      item.add_marker(pytest.mark.contract)
    elif 'Endpoints' in nodeid:
      item.add_marker(pytest.mark.api)
    elif 'Service' in nodeid:
      item.add_marker(pytest.mark.unit)


@pytest.fixture(scope='session')
def app():
  """Provide the Flask app in testing mode for pytest-native tests."""
  from app import create_app

  return create_app('TestingConfig')


@pytest.fixture()
def client(app):
  """Provide a Flask test client with an active app context."""
  with app.app_context():
    yield app.test_client()


@pytest.fixture(scope='session')
def service_base_url():
  """Optional external service URL used by contract tests."""
  return os.getenv('SERVICE_BASE_URL')