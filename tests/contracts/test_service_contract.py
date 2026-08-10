import pytest


@pytest.mark.contract
def test_service_health_contract():
  """Contract smoke test for the local service docs endpoint."""
  from app import create_app

  app = create_app('TestingConfig')
  with app.test_client() as client:
    response = client.get('/password-keeper-api/docs/')

  # Basic public contract: docs endpoint exists and is reachable.
  assert response.status_code == 200
