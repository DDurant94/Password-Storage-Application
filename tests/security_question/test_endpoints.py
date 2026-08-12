from unittest.mock import patch

import unittest
from flask import json

from tests.helpers import BaseFlaskTest
from tests.security_question.test_data import mock_question_data, mock_question_object
from utils.errorHandlers import ApiError


class TestSecurityQuestionEndpoints(BaseFlaskTest):

  @patch('controllers.securityQuestionController.securityQuestionService.save')
  def test_post_question_success(self, mock_save):
    mock_save.return_value = mock_question_object()

    response = self.client.post(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_question_validation_error(self):
    response = self.client.post('/security/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.securityQuestionController.securityQuestionService.save')
  def test_post_question_service_unavailable(self, mock_save):
    mock_save.side_effect = ApiError('Service temporarily unavailable', status_code=503)

    response = self.client.post(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 503)
    self.assertIn('Service temporarily unavailable', response.get_data(as_text=True))

  @patch('controllers.securityQuestionController.securityQuestionService.find')
  def test_get_questions_success(self, mock_find):
    mock_find.return_value = [mock_question_object()]

    response = self.client.get('/security/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.securityQuestionController.securityQuestionService.find')
  def test_get_questions_not_found(self, mock_find):
    mock_find.return_value = None

    response = self.client.get('/security/')

    self.assertEqual(response.status_code, 404)
    self.assertIn('No Security Questions found!', response.get_data(as_text=True))

  @patch('controllers.securityQuestionController.securityQuestionService.update')
  def test_put_question_success(self, mock_update):
    mock_update.return_value = mock_question_object()

    response = self.client.put(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.securityQuestionController.securityQuestionService.update')
  def test_put_question_error(self, mock_update):
    mock_update.side_effect = ValueError('Question Not Found')

    response = self.client.put(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 422)
    self.assertIn('Question Not Found', response.get_data(as_text=True))

  @patch('controllers.securityQuestionController.securityQuestionService.delete')
  def test_delete_question_success(self, mock_delete):
    mock_delete.return_value = 'successful'

    response = self.client.delete(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn('Question removed successfully', response.get_data(as_text=True))

  @patch('controllers.securityQuestionController.securityQuestionService.delete')
  def test_delete_question_not_found(self, mock_delete):
    mock_delete.return_value = None

    response = self.client.delete(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
