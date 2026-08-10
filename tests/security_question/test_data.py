from unittest.mock import MagicMock

from models.securityQuestion import SecurityQuestion


def mock_question_data():
  return {
    'question_id': 1,
    'user_id': 1,
    'question': 'Your first pet?',
    'encripted_answer': 'Milo'
  }


def mock_question_object():
  question = MagicMock(spec=SecurityQuestion)
  question.question_id = 1
  question.user_id = 1
  question.question = 'Your first pet?'
  question.encripted_answer = 'Milo'
  return question
