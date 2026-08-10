from unittest.mock import patch, MagicMock

import unittest

from services.securityQuestionService import save, find, update, delete
from tests.helpers import BaseFlaskTest, mocked_session
from tests.security_question.test_data import mock_question_data, mock_question_object


class TestSecurityQuestionService(BaseFlaskTest):

  @patch('services.securityQuestionService.encrypted')
  @patch('services.securityQuestionService.find_user')
  @patch('services.securityQuestionService.Session')
  def test_save_success(self, mock_session, mock_find_user, mock_encrypted):
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
    user = MagicMock()
    user.user_id = 1
    mock_find_user.return_value = [user, b'key']

    session_instance = mocked_session(mock_session)
    session_instance.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_question_object()

    result = delete(1, mock_question_data())

    self.assertEqual(result, 'successful')
    session_instance.delete.assert_called_once()


if __name__ == '__main__':
  unittest.main()
