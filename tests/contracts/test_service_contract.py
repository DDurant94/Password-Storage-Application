import pytest
from urllib import request


@pytest.mark.contract
def test_service_health_contract(service_base_url):
  """Contract smoke test for an externally hosted service instance."""
  if not service_base_url:
    pytest.skip('Set SERVICE_BASE_URL to run contract tests against deployed service')

  url = f"{service_base_url.rstrip('/')}/password-keeper-api/docs/"
  response = request.urlopen(url, timeout=10)

  # Basic public contract: docs endpoint exists and is reachable.
  assert response.status == 200
