from unittest.mock import patch, MagicMock

import unittest
from flask import json
from models.securityQuestion import SecurityQuestion
from services.securityQuestionService import save, find, update, delete
from tests.helpers import BaseFlaskTest, mocked_session


def mock_question_data():
  """Return valid request payload for security question endpoints."""
  return {
    'question_id': 1,
    'user_id': 1,
    'question': 'Your first pet?',
    'encripted_answer': 'Milo'
  }


def mock_question_object():
  """Return a mock SecurityQuestion object with required schema fields."""
  question = MagicMock(spec=SecurityQuestion)
  question.question_id = 1
  question.user_id = 1
  question.question = 'Your first pet?'
  question.encripted_answer = 'Milo'
  return question


class TestSecurityQuestionService(BaseFlaskTest):

  @patch('services.securityQuestionService.encrypted')
  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_encrypted):
    """Saving a new security question succeeds when under the question limit."""
    user = MagicMock()
    user.user_id = 1
    user.username = 'john'
    mock_find_user.return_value = [user, b'key']
    mock_encrypted.return_value = 'cipher-answer'

    session_instance = mocked_session(mock_session)
    session_instance.query.return_value.where.return_value.all.return_value = []

    result = save(1, mock_question_data())

    self.assertIsNotNone(result)
    self.assertEqual(result.question, 'Your first pet?')
    self.assertEqual(result.encripted_answer, 'cipher-answer')

  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_save_duplicate_question(self, mock_session, mock_find_user):
    """Saving a duplicate security question raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    existing = mock_question_object()
    session_instance = mocked_session(mock_session)
    session_instance.query.return_value.where.return_value.all.return_value = [existing]

    with self.assertRaises(ValueError) as context:
      save(1, mock_question_data())

    self.assertIn('Question already stored', str(context.exception))

  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_save_max_questions(self, mock_session, mock_find_user):
    """Saving a fourth question raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    user.username = 'john'
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.query.return_value.where.return_value.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    with self.assertRaises(ValueError) as context:
      save(1, mock_question_data())

    self.assertIn('has three questions already', str(context.exception))

  @patch('services.securityQuestionService.db.session.query')
  @patch('services.securityQuestionService.find_user')
  def test_find_none(self, mock_find_user, mock_query):
    """Finding questions returns None when no questions exist."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']
    mock_query.return_value.where.return_value.all.return_value = []

    result = find(1)

    self.assertIsNone(result)

  @patch('services.securityQuestionService.decrypted')
  @patch('services.securityQuestionService.db.session.query')
  @patch('services.securityQuestionService.find_user')
  def test_find_success(self, mock_find_user, mock_query, mock_decrypted):
    """Finding questions decrypts answers and returns records."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    question = mock_question_object()
    question.encripted_answer = 'cipher'
    mock_query.return_value.where.return_value.all.return_value = [question]
    mock_decrypted.return_value = 'Milo'

    result = find(1)

    self.assertEqual(result[0].encripted_answer, 'Milo')

  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_update_not_found(self, mock_session, mock_find_user):
    """Updating a missing security question raises ValueError."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    with self.assertRaises(ValueError) as context:
      update(1, mock_question_data())

    self.assertIn('Question Not Found', str(context.exception))

  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_delete_not_found(self, mock_session, mock_find_user):
    """Deleting a missing security question returns None."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    result = delete(1, mock_question_data())

    self.assertIsNone(result)

  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_delete_success(self, mock_session, mock_find_user):
    """Deleting an existing security question returns successful."""
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_question_object()

    result = delete(1, mock_question_data())

    self.assertEqual(result, 'successful')
    session_instance.delete.assert_called_once()


class TestSecurityQuestionEndpoints(BaseFlaskTest):

  @patch('controllers.securityQuestionController.securityQuestionService.save')
  def test_post_question_success(self, mock_save):
    """POST /security/ returns 201 when question is created."""
    mock_save.return_value = mock_question_object()

    response = self.client.post(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  def test_post_question_validation_error(self):
    """POST /security/ returns 400 for invalid payload."""
    response = self.client.post('/security/', data=json.dumps({}), content_type='application/json')

    self.assertEqual(response.status_code, 400)

  @patch('controllers.securityQuestionController.securityQuestionService.find')
  def test_get_questions_success(self, mock_find):
    """GET /security/ returns 200 when questions exist."""
    mock_find.return_value = [mock_question_object()]

    response = self.client.get('/security/')

    self.assertEqual(response.status_code, 200)

  @patch('controllers.securityQuestionController.securityQuestionService.find')
  def test_get_questions_not_found(self, mock_find):
    """GET /security/ returns 404 when no questions exist."""
    mock_find.return_value = None

    response = self.client.get('/security/')

    self.assertEqual(response.status_code, 404)
    self.assertIn('No Security Questions found!', response.get_data(as_text=True))

  @patch('controllers.securityQuestionController.securityQuestionService.update')
  def test_put_question_success(self, mock_update):
    """PUT /security/ returns 201 when update succeeds."""
    mock_update.return_value = mock_question_object()

    response = self.client.put(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)

  @patch('controllers.securityQuestionController.securityQuestionService.update')
  def test_put_question_error(self, mock_update):
    """PUT /security/ returns 422 on service error."""
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
    """DELETE /security/ returns 200 when delete succeeds."""
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
    """DELETE /security/ returns 404 when question is not found."""
    mock_delete.return_value = None

    response = self.client.delete(
      '/security/',
      data=json.dumps(mock_question_data()),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
  unittest.main()
