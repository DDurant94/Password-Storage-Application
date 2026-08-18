import unittest


"""Helper Testing"""

def mocked_session(mock_session):
  """Return the active SQLAlchemy Session mock in context-manager usage."""
  return mock_session.return_value.__enter__.return_value


class BaseFlaskTest(unittest.TestCase):
  """Shared Flask app/client setup used by service and endpoint tests."""

  def setUp(self):
    from app import create_app

    self.app = create_app('TestingConfig')
    self.client = self.app.test_client()
    self.ctx = self.app.app_context()
    self.ctx.push()

  def tearDown(self):
    self.ctx.pop()
