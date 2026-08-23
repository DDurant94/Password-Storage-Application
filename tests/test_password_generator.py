from unittest.mock import patch

from tests.helpers import BaseFlaskTest


class TestPasswordGeneratorEndpoints(BaseFlaskTest):

  @patch('controllers.passwordGeneratorController.passwordGeneratorService.generate')
  def test_get_password_generator_success(self, mock_generate):
    mock_generate.return_value = 'Generated-password-1!'

    response = self.client.get('/password-generator/')

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json(), {'password': 'Generated-password-1!'})

  @patch('controllers.passwordGeneratorController.passwordGeneratorService.generate')
  def test_get_password_generator_service_error(self, mock_generate):
    mock_generate.side_effect = ValueError('Unable to generate password')

    response = self.client.get('/password-generator/')

    self.assertEqual(response.status_code, 422)
    self.assertIn('Unable to generate password', response.get_data(as_text=True))
